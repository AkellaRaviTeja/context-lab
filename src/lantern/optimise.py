"""Letting a program rewrite the standing orders: propose, score, keep, on a split it can see.

Chapter 22 (amendment A1, decision 0004). A proposer (the model) is shown the standing orders
and the questions they failed on the training split, and writes a revised version. The
revision is scored on the training split and kept only if it passes more than the best so far.
The best is then scored once on a held-out split the proposer never saw. The gap between the
two is what it learned that holds only on the cases it saw.

Nothing here calls a model directly: `propose` takes `chat=`, and `optimise` takes the
proposer and the scorer as functions, so the loop is tested offline.
"""

from __future__ import annotations

import random
import re
from collections.abc import Callable
from typing import Any

Result = dict[str, Any]
RULE = re.compile(r"^\s*(\d+)\.\s+\S", re.M)

PROPOSE = """You maintain the standing orders of LANTERN, an analysis workstation. Below are
the current standing orders, then questions that LANTERN answered wrongly with them, each with
its answer and what a correct answer had to contain.

Write a revised version of the standing orders that would make LANTERN answer questions like
these correctly. Change, add or remove at least one rule: a copy of the current orders is
not scored. Keep it a numbered list of rules, one rule a line, under the same title.
Reply with the standing orders only.{must}{tried}

Current standing orders:
{orders}

Questions answered wrongly:
{failures}"""


def split(questions: list[dict[str, Any]], *, train: int, held: int, seed: int
          ) -> tuple[list[str], list[str]]:
    """Question ids for a training split and a held-out split: from every slice, `train`
    ids and then `held` more, chosen by a seeded shuffle of that slice, so both splits have
    every kind of question and the same seed gives the same split. A slice with fewer
    questions gives what it has, training first. No id is in both."""
    by_slice: dict[str, list[str]] = {}
    for q in questions:
        by_slice.setdefault(q["slice"], []).append(q["id"])
    rng = random.Random(seed)
    tr: list[str] = []
    ho: list[str] = []
    for ids in by_slice.values():
        ids = list(ids)
        rng.shuffle(ids)
        tr += ids[:train]
        ho += ids[train:train + held]
    order = {q["id"]: i for i, q in enumerate(questions)}
    return sorted(tr, key=order.get), sorted(ho, key=order.get)


def expected(expect: dict[str, Any]) -> str:
    """What the grader needs, in words: "contains PNL-TR-0618-1", "begins with no"."""
    parts = []
    if expect.get("all"):
        parts.append("contains " + " and ".join(map(str, expect["all"])))
    if expect.get("any"):
        parts.append("contains one of " + ", ".join(map(str, expect["any"])))
    if "starts" in expect:
        parts.append(f"begins with {expect['starts']!r}")
    if expect.get("or_not_in_evidence"):
        parts.append("or says 'not in evidence'")
    if expect.get("none"):
        parts.append("does not contain " + ", ".join(map(str, expect["none"])))
    return "; ".join(parts) or "(no condition)"


def failures(results: list[Result], questions: dict[str, dict[str, Any]]) -> list[Result]:
    """The failed results, each with what the grader expected."""
    return [{**r, "expected": expected(questions[r["id"]]["expect"])}
            for r in results if not r["passed"]]


def rules(text: str) -> int:
    """How many numbered rules a standing-orders text has."""
    return len(RULE.findall(text))


def clean(text: str) -> str:
    """A proposal as standing orders: code fences and anything before the title taken off."""
    text = re.sub(r"^```\w*\s*$", "", text.strip(), flags=re.M).strip()
    start = text.find("# ")
    return (text[start:] if start > 0 else text).strip() + "\n"


def propose(orders: str, failed: list[Result], *, chat: Callable[..., Any], seed: int = 7,
            must_keep: tuple[str, ...] = (), tried: tuple[str, ...] = (),
            temperature: float = 0.7, max_tokens: int = 1400) -> str:
    """One revision of the standing orders from the model, given the failures it may see and
    the rules it already tried that were not kept. The proposer samples warmer than LANTERN
    (0.7 against 0.2): at 0.2 the first live run wrote the same copy three times."""
    lines = "\n".join(f"- {f['question']}\n  LANTERN answered: {f['answer'][:240]!r}\n"
                      f"  A correct answer {f['expected']}." for f in failed) or "(none)"
    must = ("\nThe revision must keep these words exactly: "
            + "; ".join(f'"{m}"' for m in must_keep) + ".") if must_keep else ""
    before = ("\n\nAlready tried and not kept (do not write these again):\n"
              + "\n".join(f"- {line}" for t in tried for line in rule_lines(t)
                           if line not in rule_lines(orders))) if tried else ""
    r = chat(PROPOSE.format(orders=orders.strip(), failures=lines, must=must, tried=before),
             seed=seed, temperature=temperature, max_tokens=max_tokens)
    return clean(r.text)


def rule_lines(text: str) -> list[str]:
    """The numbered rules of a text, each with its spacing collapsed: what a revision says."""
    return [" ".join(line.split()) for line in text.splitlines() if RULE.match(line)]


def same_rules(a: str, b: str) -> bool:
    """Two texts with the same rules, in the same order: a title or a space is not a change."""
    return rule_lines(a) == rule_lines(b)


def optimise(start: str, *, propose: Callable[[str, list[Result]], str],
             score: Callable[[str], list[Result]], rounds: int,
             start_results: list[Result] | None = None, least_rules: int = 5
             ) -> list[dict[str, Any]]:
    """Propose, score, keep, for `rounds` rounds, on the training split only.

    `score(orders)` asks the training questions with those orders and returns graded results;
    `propose(orders, failed)` writes a revision from the best orders so far and their failed
    results. A revision is kept only if it passes more than the best so far. One with fewer
    than `least_rules` numbered rules, or the same rules as any earlier round (spacing and
    title aside), is not scored.

    Returns the history: round 0 is `start` (scored unless `start_results` is given), then
    one record a round with "orders", "passed" (None when not scored), "results", "kept" and
    "why". The best is the last record with kept True.
    """
    first = start_results if start_results is not None else score(start)
    history = [{"round": 0, "orders": start, "passed": sum(r["passed"] for r in first),
                "results": first, "kept": True, "why": "the standing orders as they are"}]
    best = history[0]
    for n in range(1, rounds + 1):
        failed = [r for r in best["results"] if not r["passed"]]
        candidate = propose(best["orders"], failed)
        record: dict[str, Any] = {"round": n, "orders": candidate, "passed": None,
                                  "results": [], "kept": False}
        if rules(candidate) < least_rules:
            record["why"] = f"not scored: {rules(candidate)} numbered rules"
        elif any(same_rules(candidate, h["orders"]) for h in history):
            twin = next(h["round"] for h in history if same_rules(candidate, h["orders"]))
            record["why"] = f"not scored: the same rules as round {twin}"
        else:
            record["results"] = score(candidate)
            record["passed"] = sum(r["passed"] for r in record["results"])
            record["kept"] = record["passed"] > best["passed"]
            record["why"] = (f"kept: {record['passed']} against {best['passed']}"
                             if record["kept"] else
                             f"dropped: {record['passed']} against {best['passed']}")
        history.append(record)
        if record["kept"]:
            best = record
    return history


def best(history: list[dict[str, Any]]) -> dict[str, Any]:
    return [h for h in history if h["kept"]][-1]


def leaked(orders: str, start: str, questions: list[dict[str, Any]]) -> list[str]:
    """Answers the grader looks for, from these questions, that are in `orders` and were not
    in `start`: what a revision copied from the cases it was shown."""
    def norm(t: str) -> str:
        return re.sub(r"(?<=\d),(?=\d)", "", t).lower()
    found = []
    for q in questions:
        e = q["expect"]
        for v in [*e.get("all", []), *e.get("any", [])]:
            v = str(v)
            if len(v) >= 4 and norm(v) in norm(orders) and norm(v) not in norm(start) \
                    and v not in found:
                found.append(v)
    return found


__all__ = ["PROPOSE", "best", "clean", "expected", "failures", "leaked", "optimise",
           "propose", "rule_lines", "rules", "same_rules", "split"]
