"""Compaction that keeps who paid whom.

Chapter 10 builds three compactors, each a `before_request` hook for `lantern.agent.run`. When
the conversation passes a threshold, everything after the task is replaced by one message:

- `free_text`: a paragraph the model writes (Case File 02 chapter 17);
- `with_schema`: a form the model fills in, checked in code against the tool results and
  refused when a field is missing or wrong;
- `from_source`: the same form filled in by code, from the tool results themselves.

Every compactor keeps a ledger of the tool results it has seen. The ledger is outside the
window: it is what the check compares the model's form against.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

Messages = list[dict[str, Any]]
BANK_WORDS = ("Bank",)
HEAD = "Work so far, compacted. The turns it replaces are no longer in front of you.\n"
FREE = ("Summarise the work so far for yourself, in one paragraph, so that you can carry on "
        "the task from the summary alone. The task was:\n")
FORM = ("Fill in the form for the work so far, so that you can carry on the task from the form "
        "alone. Reply with JSON only: {\"flows\": [{\"payer\": str, \"payee\": str, "
        "\"payments\": int, \"total\": str, \"source\": str}], \"accounts_read\": [str], "
        "\"open_questions\": [str]}. A flow is one payer paying one payee; source is the file "
        "it was read from; accounts_read lists every file opened. The task was:\n")
SCHEMA = {
    "type": "object", "required": ["flows", "accounts_read", "open_questions"],
    "properties": {
        "flows": {"type": "array", "items": {
            "type": "object", "required": ["payer", "payee", "payments", "total", "source"],
            "properties": {"payer": {"type": "string"}, "payee": {"type": "string"},
                           "payments": {"type": "integer"}, "total": {"type": "string"},
                           "source": {"type": "string"}}}},
        "accounts_read": {"type": "array", "items": {"type": "string"}},
        "open_questions": {"type": "array", "items": {"type": "string"}}},
}


@dataclass
class Log:
    """What a compactor did during one run."""

    compactions: int = 0
    refused: int = 0
    problems: list[list[str]] = field(default_factory=list)
    states: list[str] = field(default_factory=list)
    kept: list[tuple[int, int]] = field(default_factory=list)  # (flows kept whole, flows seen)


def record(messages: Messages, ledger: dict[str, dict[str, Any]]) -> None:
    """Add every digest among the tool results to the ledger, by file."""
    for m in messages:
        if m["role"] != "tool":
            continue
        try:
            result = json.loads(m["content"])
        except ValueError:
            continue
        if isinstance(result, dict) and "paid_out_to" in result:
            ledger[result["statement"]] = result


def seen_flows(ledger: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Every payment to a payee that is not a bank, from the ledger, as the form writes it."""
    return [{"payer": d["holder"], "payee": p["payee"], "payments": p["payments"],
             "total": p["total"], "source": file}
            for file, d in ledger.items() for p in d["paid_out_to"]
            if not any(w in p["payee"] for w in BANK_WORDS)]


AMOUNT = re.compile(r"(?<![\d.])\d[\d,]*(?:\.\d+)?(?![\d])")


def number(value: Any) -> float | None:
    """A figure as a number, or None. Model output may be a string, a number or anything else:
    "1,873,000.00", 1873000 and "1873000" are the same figure; None, a list or "n/a" is none."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except ValueError:
            return None
    return None


def amounts(text: str) -> set[float]:
    """Every whole figure written in a text, as numbers. A figure is matched whole: 2262000 is
    not found inside 22620000, and 1,873,000 equals 1873000.00."""
    return {float(m.replace(",", "")) for m in AMOUNT.findall(text)}


def survived(text: str, flows: list[dict[str, Any]]) -> int:
    """How many seen flows are still whole in a text: payer, payee and total all present, the
    total as a whole figure."""
    figures = amounts(text)
    return sum(f["payer"] in text and f["payee"] in text and number(f["total"]) in figures
               for f in flows)


def all_pairs(ledger: dict[str, dict[str, Any]]) -> set[tuple[str, str]]:
    """Every (payer, payee) any tool result holds, banks included."""
    return {(d["holder"], p["payee"]) for d in ledger.values() for p in d["paid_out_to"]}


def check(state: Any, ledger: dict[str, dict[str, Any]]) -> list[str]:
    """Problems with a filled-in form, against the ledger. An empty list means it is kept.

    A flow to a bank is not required (bank charges are not hops), but it must still be in a tool
    result: an invented flow is refused whoever the payee is."""
    if not isinstance(state, dict):
        return ["the form is not a JSON object"]
    problems = []
    want = {(f["payer"], f["payee"]): f for f in seen_flows(ledger)}
    returned = all_pairs(ledger)
    got = {}
    flows = state.get("flows", [])
    for i, f in enumerate(flows if isinstance(flows, list) else [], 1):
        if not isinstance(f, dict):
            problems.append(f"flow {i} is not an object")
            continue
        missing = [k for k in ("payer", "payee", "payments", "total", "source")
                   if f.get(k) in (None, "", [])]
        if missing:
            problems.append(f"flow {i} has no {', '.join(missing)}")
            continue
        got[(str(f["payer"]), str(f["payee"]))] = f
    for key, f in want.items():
        g = got.get(key)
        if g is None:
            problems.append(f"missing: {key[0]} paid {key[1]} ({f['source']})")
        elif number(g["total"]) != number(f["total"]):
            problems.append(f"{key[0]} paid {key[1]}: total {g['total']}, the tool said "
                            f"{f['total']}")
        elif number(g["payments"]) != f["payments"]:
            problems.append(f"{key[0]} paid {key[1]}: {g['payments']} payments, the tool said "
                            f"{f['payments']}")
    for key in got:
        if key not in returned:
            problems.append(f"not in any tool result: {key[0]} paid {key[1]}")
    read = state.get("accounts_read", [])
    unread = sorted(set(ledger) - set(read if isinstance(read, list) else []))
    if unread:
        problems.append(f"accounts_read leaves out {', '.join(unread)}")
    return problems


def _split(messages: Messages) -> tuple[Messages, Messages, str]:
    """The head a compaction never touches (every leading system message and the first user
    message, the task), the turns after it, and the task text. Found by role, not position: a
    conversation may open with two system messages, or with none."""
    i = 0
    while i < len(messages) and messages[i]["role"] == "system":
        i += 1
    if i >= len(messages) or messages[i]["role"] != "user":
        raise ValueError("a conversation to compact must hold its task as the first user "
                         "message after the system messages")
    return messages[:i + 1], messages[i + 1:], messages[i]["content"]


def _head(messages: Messages) -> tuple[Messages, str]:
    """The system messages and the task, which a compaction never touches, and the task text."""
    head, _, task = _split(messages)
    return head, task


def _rendered(messages: Messages) -> str:
    """The turns to be compacted, as text for the model that will compact them."""
    lines = []
    for m in _split(messages)[1]:
        said = m.get("content") or json.dumps([c["function"] for c in m.get("tool_calls", [])])
        lines.append(f"{m['role']}: {said}")
    return "\n".join(lines)


def _due(messages: Messages, threshold: int, count: Callable[[str], int]) -> bool:
    size = sum(count(m.get("content") or json.dumps(m.get("tool_calls", []))) for m in messages)
    return size > threshold and sum(m["role"] == "tool" for m in messages) >= 2


def _compacted(head: Messages, state: str) -> Messages:
    return [*head, {"role": "user", "content": HEAD + state + "\nCarry on with the task."}]


def free_text(chat: Callable[..., Any], threshold: int, count: Callable[[str], int],
              log: Log, ledger: dict[str, dict[str, Any]] | None = None
              ) -> Callable[[Messages], Messages]:
    """Case File 02's compaction: the model summarises the turns in a paragraph."""
    ledger = {} if ledger is None else ledger

    def hook(messages: Messages) -> Messages:
        record(messages, ledger)
        if not _due(messages, threshold, count):
            return messages
        head, task = _head(messages)
        text = chat(_rendered(messages), system=FREE + task, seed=7, max_tokens=400).text
        flows = seen_flows(ledger)
        log.compactions += 1
        log.states.append(text)
        log.kept.append((survived(text, flows), len(flows)))
        return _compacted(head, text)
    return hook


def with_schema(chat: Callable[..., Any], threshold: int, count: Callable[[str], int],
                log: Log, retries: int = 2, ledger: dict[str, dict[str, Any]] | None = None
                ) -> Callable[[Messages], Messages]:
    """The model fills in the form; code checks it against the ledger and refuses a bad one.
    After `retries` refusals the form is filled in from the ledger."""
    ledger = {} if ledger is None else ledger

    def hook(messages: Messages) -> Messages:
        record(messages, ledger)
        if not _due(messages, threshold, count):
            return messages
        head, task = _head(messages)
        ask = _rendered(messages)
        state: dict[str, Any] = {}
        for _ in range(retries + 1):
            try:
                state = chat(ask, system=FORM + task, seed=7, max_tokens=900,
                             format=SCHEMA).json()
                problems = check(state, ledger)
            except (ValueError, TypeError):
                problems = ["the reply was not JSON"]
            if not problems:
                break
            log.refused += 1
            log.problems.append(problems)
            ask = (_rendered(messages) + "\n\nYour last form was refused: " + "; ".join(problems)
                   + ". Fill it in again from the tool results above.")
        else:
            state = filled(ledger)
        text = json.dumps(state, indent=1)
        flows = seen_flows(ledger)
        log.compactions += 1
        log.states.append(text)
        log.kept.append((survived(text, flows), len(flows)))
        return _compacted(head, text)
    return hook


def filled(ledger: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """The form filled in by code from the ledger: nothing in it was written by a model."""
    return {"flows": seen_flows(ledger), "accounts_read": sorted(ledger), "open_questions": []}


def from_source(threshold: int, count: Callable[[str], int], log: Log,
                ledger: dict[str, dict[str, Any]] | None = None
                ) -> Callable[[Messages], Messages]:
    """The form filled in by code, from the tool results themselves, every time."""
    ledger = {} if ledger is None else ledger

    def hook(messages: Messages) -> Messages:
        record(messages, ledger)
        if not _due(messages, threshold, count):
            return messages
        head, _ = _head(messages)
        text = json.dumps(filled(ledger), indent=1)
        flows = seen_flows(ledger)
        log.compactions += 1
        log.states.append(text)
        log.kept.append((survived(text, flows), len(flows)))
        return _compacted(head, text)
    return hook


def _reported(report: str, flow: dict[str, Any]) -> bool:
    """A FLOW line for this payer and payee holds this total, as a whole figure."""
    for line in report.splitlines():
        if f"{flow['payer']} -> {flow['payee']}" in line and number(flow["total"]) in amounts(line):
            return True
    return False


def report_covers(ledger: dict[str, dict[str, Any]], skip: tuple[str, ...] = ()
                  ) -> Callable[[str], str | None]:
    """A check for agent.run(until=...): a report must hold every flow in the ledger.

    A compacted state the model was given is not a finding it will report unasked. This check
    compares the report with the ledger and sends back the flows it leaves out. `skip` names
    payees the task said to ignore.
    """
    def check(report: str) -> str | None:
        left = [f for f in seen_flows(ledger) if f["payee"] not in skip
                and not _reported(report, f)]
        if not left:
            return None
        return ("Not done. Your report leaves out flows you have already found: "
                + "; ".join(f"{f['payer']} -> {f['payee']} | {f['payments']} payments | total "
                            f"{f['total']}" for f in left)
                + ". Give the whole report again, every FLOW line, ending with DONE.")
    return check


# ---- probes: forms whose answer is known, for a check written by hand ----------------------

PROBE_LEDGER = {
    "a.csv": {"holder": "Corvane Trading", "paid_out_to": [
        {"payee": "Arden Logistics", "payments": 3, "total": "84,000.00"},
        {"payee": "Harbour Bank", "payments": 1, "total": "12.50"}]},
    "b.csv": {"holder": "Arden Logistics", "paid_out_to": [
        {"payee": "Tidewater Holdings", "payments": 2, "total": "80,000.00"}]},
}
_GOOD = [{"payer": "Corvane Trading", "payee": "Arden Logistics", "payments": 3,
          "total": "84,000.00", "source": "a.csv"},
         {"payer": "Arden Logistics", "payee": "Tidewater Holdings", "payments": 2,
          "total": "80000", "source": "b.csv"}]


def _form(flows: list[dict[str, Any]], read: tuple[str, ...] = ("a.csv", "b.csv")) -> dict:
    return {"flows": flows, "accounts_read": list(read), "open_questions": []}


PROBES: list[tuple[str, Any]] = [
    ("not a JSON object", "Corvane paid Arden 84,000.00"),
    ("a flow left out", _form(_GOOD[:1])),
    ("a total changed", _form([_GOOD[0], {**_GOOD[1], "total": "8,000.00"}])),
    ("a count changed", _form([{**_GOOD[0], "payments": 2}, _GOOD[1]])),
    ("a flow with no source", _form([_GOOD[0], {**_GOOD[1], "source": ""}])),
    ("a flow no tool returned", _form([*_GOOD, {"payer": "Tidewater Holdings",
                                                 "payee": "Pellmar & Co", "payments": 1,
                                                 "total": "80,000.00", "source": "b.csv"}])),
    ("an account left out of accounts_read", _form(_GOOD, read=("a.csv",))),
]


def probe(check: Callable[[Any, dict[str, dict[str, Any]]], list[str]]) -> dict[str, Any]:
    """Run `check` on a right form (it must be kept) and on PROBES (each must be refused).

    The numbers say whether a check works before any model fills in a form: a check that
    keeps everything catches none of the probes, one that refuses everything keeps no form."""
    caught = [name for name, form in PROBES if check(form, PROBE_LEDGER)]
    return {"probes": len(PROBES), "caught": len(caught),
            "missed": [n for n, _ in PROBES if n not in caught],
            "kept_good": not check(_form(_GOOD), PROBE_LEDGER)}
