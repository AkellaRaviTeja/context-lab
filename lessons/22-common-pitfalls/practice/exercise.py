"""Chapter 22 exercise: let a program rewrite the standing orders, and check it honestly.

Write `split`, which cuts the signed questions into a training split and a held-out split, and
`optimise`, the loop of propose, score and keep that sees only the training split. The tests
hand it a proposer and a scorer that are plain functions (and once a scripted model), so they
run offline. When they pass, `make lesson N=22 ARGS=--mine` runs the chapter's loop on yours,
with qwen3:8b as the proposer.
"""

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
    questions gives what it has, training first. No id is in both. Each list is in the
    order the questions were given."""
    # TODO 1: group the ids by q["slice"], keeping the order the slices first appear.
    # TODO 2: rng = random.Random(seed); shuffle each slice's ids with it, in slice order.
    # TODO 3: the first `train` go to training, the next `held` to held out.
    # TODO 4: sort both lists back into the questions' order.
    raise NotImplementedError("write split")


def optimise(start: str, *, propose: Callable[[str, list[Result]], str],
             score: Callable[[str], list[Result]], rounds: int,
             start_results: list[Result] | None = None, least_rules: int = 5
             ) -> list[dict[str, Any]]:
    """Propose, score, keep, for `rounds` rounds, on the training split only.

    `score(orders)` asks the training questions with those orders and returns graded results
    (dicts with "id" and "passed"); `propose(orders, failed)` writes a revision from the best
    orders so far and their failed results. A revision is kept only if it passes more than
    the best so far. One with fewer than `least_rules` numbered rules, or the same text as the
    best (ignoring surrounding whitespace), is not scored.

    Returns the history: round 0 is `start` (scored unless `start_results` is given), then
    one record a round, each a dict with "round", "orders", "passed" (None when not scored),
    "results" ([] when not scored), "kept" and "why" (a few words; begin with "kept",
    "dropped" or "not scored"). Round 0 has kept True. The best is the last record with kept
    True.
    """
    # TODO 5: round 0: score start (or use start_results); it is the best so far.
    # TODO 6: each round: propose from the best's orders and the best's failed results.
    # TODO 7: skip scoring a malformed or unchanged revision; otherwise score it.
    # TODO 8: keep it only if it passes strictly more than the best; then it is the best.
    raise NotImplementedError("write optimise")
