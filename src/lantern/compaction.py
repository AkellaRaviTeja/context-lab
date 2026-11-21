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


def survived(text: str, flows: list[dict[str, Any]]) -> int:
    """How many seen flows are still whole in a text: payer, payee and total all present."""
    plain = text.replace(",", "")
    return sum(f["payer"] in plain and f["payee"] in plain
               and f["total"].replace(".00", "") in plain for f in flows)


def check(state: dict[str, Any], ledger: dict[str, dict[str, Any]]) -> list[str]:
    """Problems with a filled-in form, against the ledger. An empty list means it is kept."""
    problems = []
    want = {(f["payer"], f["payee"]): f for f in seen_flows(ledger)}
    got = {}
    for i, f in enumerate(state.get("flows", []), 1):
        missing = [k for k in ("payer", "payee", "payments", "total", "source") if not f.get(k)]
        if missing:
            problems.append(f"flow {i} has no {', '.join(missing)}")
            continue
        got[(f["payer"], f["payee"])] = f
    for key, f in want.items():
        g = got.get(key)
        if g is None:
            problems.append(f"missing: {key[0]} paid {key[1]} ({f['source']})")
        elif float(str(g["total"]).replace(",", "")) != float(f["total"]):
            problems.append(f"{key[0]} paid {key[1]}: total {g['total']}, the tool said "
                            f"{f['total']}")
        elif int(g["payments"]) != f["payments"]:
            problems.append(f"{key[0]} paid {key[1]}: {g['payments']} payments, the tool said "
                            f"{f['payments']}")
    for key in got:
        if key not in want and not any(w in key[1] for w in BANK_WORDS):
            problems.append(f"not in any tool result: {key[0]} paid {key[1]}")
    unread = sorted(set(ledger) - set(state.get("accounts_read", [])))
    if unread:
        problems.append(f"accounts_read leaves out {', '.join(unread)}")
    return problems


def _head(messages: Messages) -> tuple[Messages, str]:
    """The system message and the task, which a compaction never touches, and the task text."""
    head = [m for m in messages[:2]]
    return head, next(m["content"] for m in head if m["role"] == "user")


def _rendered(messages: Messages) -> str:
    """The turns to be compacted, as text for the model that will compact them."""
    lines = []
    for m in messages[2:]:
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
            except ValueError:
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


def report_covers(ledger: dict[str, dict[str, Any]], skip: tuple[str, ...] = ()
                  ) -> Callable[[str], str | None]:
    """A check for agent.run(until=...): a report must hold every flow in the ledger.

    A compacted state the model was given is not a finding it will report unasked. This check
    compares the report with the ledger and sends back the flows it leaves out. `skip` names
    payees the task said to ignore.
    """
    def check(report: str) -> str | None:
        plain = report.replace(",", "")
        left = [f for f in seen_flows(ledger) if f["payee"] not in skip
                and not (f"{f['payer']} -> {f['payee']}" in plain
                         and f["total"].replace(".00", "") in plain)]
        if not left:
            return None
        return ("Not done. Your report leaves out flows you have already found: "
                + "; ".join(f"{f['payer']} -> {f['payee']} | {f['payments']} payments | total "
                            f"{f['total']}" for f in left)
                + ". Give the whole report again, every FLOW line, ending with DONE.")
    return check
