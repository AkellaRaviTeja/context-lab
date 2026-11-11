"""Chapter 02 reference solution: the grader. Code decides whether an answer meets the record."""

from __future__ import annotations

import re
from typing import Any

NOT_IN_EVIDENCE = "not in evidence"


def normal(text: str) -> str:
    """Lower case, with the commas taken out of numbers: 1,183,369.26 reads as 1183369.26."""
    return re.sub(r"(?<=\d),(?=\d)", "", text).lower()


def says(text: str, value: str) -> bool:
    """Is `value` in `text` as a whole word or number, not as part of a longer one?"""
    return re.search(rf"(?<![\w.]){re.escape(normal(value))}(?!\w)", normal(text)) is not None


def grade(answer: str, expect: dict[str, Any]) -> bool:
    """Does the answer meet what the signed record expects? Every condition given must hold."""
    if not answer.strip():
        return False
    if expect.get("or_not_in_evidence") and says(answer, NOT_IN_EVIDENCE):
        return True
    words = re.findall(r"[a-z]+", answer.lower())
    if "starts" in expect and (not words or words[0] != expect["starts"]):
        return False
    if not all(says(answer, v) for v in expect.get("all", [])):
        return False
    if "any" in expect and not any(says(answer, v) for v in expect["any"]):
        return False
    return not any(normal(v) in normal(answer) for v in expect.get("none", []))
