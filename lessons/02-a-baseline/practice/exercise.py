"""Chapter 02 exercise: the grader. Code decides whether an answer meets the signed record.

Grade it with `make exercise N=02`. The tests pass in answers as text, so no model is needed.
When it passes, `make lesson N=02 ARGS=--mine` scores LANTERN's context with your grader.
"""

from __future__ import annotations

import re
from typing import Any

NOT_IN_EVIDENCE = "not in evidence"


def normal(text: str) -> str:
    """Lower case, with the commas taken out of numbers: 1,183,369.26 reads as 1183369.26."""
    # TODO 1: remove a comma only where it sits between two digits, then lower-case.
    raise NotImplementedError("write normal")


def says(text: str, value: str) -> bool:
    """Is `value` in `text` as a whole word or number, not as part of a longer one?

    "5" is in "5 transfers" and not in "PNL-S4-005". "3600" is in "3,600.00" and not in
    "36,000.00". Compare the normal() form of both.
    """
    # TODO 2: search for the value with nothing word-like (or a decimal point) just before it
    #         and nothing word-like just after it. `re.escape` the value.
    raise NotImplementedError("write says")


def grade(answer: str, expect: dict[str, Any]) -> bool:
    """Does the answer meet what the signed record expects? Every condition given must hold.

    `expect` may hold any of:
      "starts": "yes" or "no"       the first word of the answer, ignoring case and punctuation
      "all": [values]               every value is said
      "any": [values]               at least one value is said
      "none": [phrases]             none of these appears anywhere (plain substring, normal form)
      "or_not_in_evidence": True    an answer that says "not in evidence" passes whatever else
    An empty answer never passes.
    """
    # TODO 3: empty answer -> False.
    # TODO 4: or_not_in_evidence, then starts, all, any, none, in that order.
    raise NotImplementedError("write grade")
