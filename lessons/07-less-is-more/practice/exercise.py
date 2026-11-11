"""Chapter 07 exercise: a cut-off for the context builder that records what it left out.

Grade it with `make exercise N=07`. The tests pass in pages as text, so no model is needed.
When it passes, `make lesson N=07 ARGS=--mine` builds each question's context with your select.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Words too common in this inquiry to tell one page from another.
COMMON = frozenset("""the a an of to in on for and or by is was were are be it its this that
with from at as not no what which who how much many did does do into out after before
pellmar nominees ltd account""".split())


@dataclass(frozen=True)
class Page:
    path: str
    title: str
    text: str


def terms(text: str) -> set[str]:
    """The telling terms of a text: words and figures, lower case, less the common ones.

    Given: "296,400.00" and "296400.00" are the same term, and "ICB-77-10458." loses its full
    stop.
    """
    words = re.findall(r"[a-z0-9][a-z0-9.,-]*[a-z0-9]|[a-z0-9]", text.lower())
    return {w.replace(",", "") for w in words} - COMMON


def overlap(question: str, page: Page) -> float:
    """The share of the question's telling terms that the page contains, from 0.0 to 1.0.

    A question with no telling terms scores 0.0 against every page.
    """
    # TODO 1: terms of the question, terms of page.text, the size of what they share over the
    #         size of the question's.
    raise NotImplementedError("write overlap")


def select(pages: list[Page], question: str, threshold: float
           ) -> tuple[list[Page], list[tuple[str, float]]]:
    """The pages admitted for this question, and (path, score) for every page left out.

    A page is admitted when its overlap is at least the threshold. Both lists keep the order
    the pages came in. Scores in the second list are rounded to two places.
    """
    # TODO 2: score each page once; admit it or record it. Nothing is dropped without a record.
    raise NotImplementedError("write select")
