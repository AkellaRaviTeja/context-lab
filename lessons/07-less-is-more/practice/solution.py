"""Chapter 07 reference solution: a cut-off that records what it left out."""

from __future__ import annotations

import re
from dataclasses import dataclass

COMMON = frozenset("""the a an of to in on for and or by is was were are be it its this that
with from at as not no what which who how much many did does do into out after before
pellmar nominees ltd account""".split())


@dataclass(frozen=True)
class Page:
    path: str
    title: str
    text: str


def terms(text: str) -> set[str]:
    """The telling terms of a text: words and figures, lower case, less the common ones."""
    words = re.findall(r"[a-z0-9][a-z0-9.,-]*[a-z0-9]|[a-z0-9]", text.lower())
    return {w.replace(",", "") for w in words} - COMMON


def overlap(question: str, page: Page) -> float:
    """The share of the question's telling terms that the page contains."""
    asked = terms(question)
    return len(asked & terms(page.text)) / len(asked) if asked else 0.0


def select(pages: list[Page], question: str, threshold: float
           ) -> tuple[list[Page], list[tuple[str, float]]]:
    """The pages admitted for this question, and (path, score) for every page left out."""
    kept, left_out = [], []
    for p in pages:
        score = overlap(question, p)
        if score >= threshold:
            kept.append(p)
        else:
            left_out.append((p.path, round(score, 2)))
    return kept, left_out
