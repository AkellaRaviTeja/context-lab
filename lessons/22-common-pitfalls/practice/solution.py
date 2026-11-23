"""Chapter 22 solution: a training split and a held-out split, and the propose, score, keep
loop that only ever sees the first."""

from __future__ import annotations

import random
import re
from collections.abc import Callable
from typing import Any

Result = dict[str, Any]
RULE = re.compile(r"^\s*(\d+)\.\s+\S", re.M)


def rules(text: str) -> int:
    """How many numbered rules a standing-orders text has."""
    return len(RULE.findall(text))


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


def optimise(start: str, *, propose: Callable[[str, list[Result]], str],
             score: Callable[[str], list[Result]], rounds: int,
             start_results: list[Result] | None = None, least_rules: int = 5
             ) -> list[dict[str, Any]]:
    """Propose, score, keep, for `rounds` rounds, on the training split only.

    `score(orders)` asks the training questions with those orders and returns graded results;
    `propose(orders, failed)` writes a revision from the best orders so far and their failed
    results. A revision is kept only if it passes more than the best so far. One with fewer
    than `least_rules` numbered rules, or the same text as the best, is not scored.

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
        elif candidate.strip() == best["orders"].strip():
            record["why"] = "not scored: the same as the best so far"
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
