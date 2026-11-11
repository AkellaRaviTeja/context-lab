"""Pages on file: true documents that may or may not help with the question in hand.

Chapter 07 adds them to the context and measures what they do. `select()` is the cut-off it
builds: a page is admitted only if it shares enough of the question's own terms, and every
page left out is recorded with its score.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from lantern import case
from lantern.context import SYSTEM, Section

NAME = "pages on file"
# Words too common in this inquiry to tell one page from another.
COMMON = frozenset("""the a an of to in on for and or by is was were are be it its this that
with from at as not no what which who how much many did does do into out after before
pellmar nominees ltd account""".split())


@dataclass(frozen=True)
class Page:
    path: str
    title: str
    text: str


def load(kind: str) -> list[Page]:
    """The pages under case/pages/<kind>, in file order."""
    out = []
    for path in case.files(f"pages/{kind}"):
        text = path.read_text(encoding="utf-8")
        out.append(Page(f"pages/{kind}/{path.name}", text.splitlines()[0].lstrip("# "), text))
    return out


def with_pages(parts: list[Section], pages: list[Page]) -> list[Section]:
    """The sections with these pages added to the system message, after the summaries."""
    if not pages:
        return list(parts)
    section = Section(NAME, SYSTEM, "# Pages on file\n\n" + "\n".join(p.text for p in pages))
    at = max(i for i, s in enumerate(parts) if s.where == SYSTEM) + 1
    return [*parts[:at], section, *parts[at:]]


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
