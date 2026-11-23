"""Chapter 15 exercise: the check that refuses a reader's report the main agent cannot rely on.

Grade it with `make exercise N=15`. The tests pass in reports as plain text, so no model is
needed. When it passes, `make lesson N=15 ARGS=--mine` runs every reader through your check:
a report it refuses is sent back to the reader, and one refused again never reaches the main
context.
"""

from __future__ import annotations

import re
from typing import Any

MAX_LINES = 5
NONE_WORDS = {"none", "nothing", "no pages", "-", "n/a"}
LINE = re.compile(r"^\s*[-*]*\s*LINE:\s*(.+?)\s*->\s*(.+?)\s*\|\s*(\d+)\s*payments?\s*\|\s*"
                  r"total\s*([\d,]+(?:\.\d+)?)\s*(?:\|\s*(.*))?$", re.I | re.M)
NOT_READ = re.compile(r"^\s*[-*]*\s*NOT READ:\s*(.*)$", re.I | re.M)
PAGE_ID = re.compile(r"[a-z][a-z-]*\.p\d+", re.I)


def parse(report: str) -> tuple[list[dict[str, Any]], list[str] | None]:
    """Given: the LINE lines of a report, and the pages its NOT READ line names.

    Each line is {"payer", "payee", "payments", "total", "sources"}, where sources is the page
    ids after "source:". The second value is None when there is no NOT READ line at all, and
    an empty list when the line names no pages (as "NOT READ: none" does).
    """
    lines = [{"payer": a.strip(" *"), "payee": b.strip(" *"), "payments": int(n),
              "total": float(t.replace(",", "")), "sources": PAGE_ID.findall(rest or "")}
             for a, b, n, t, rest in LINE.findall(report)]
    m = NOT_READ.search(report)
    return lines, None if m is None else PAGE_ID.findall(m.group(1))


def check_report(report: str, page_ids: list[str]) -> list[str]:
    """What is wrong with a reader's report, one string a problem; [] when it may be relied on.

    `page_ids` are the pages the reader was given, such as ["corvane-trading.p1", ...]. Page
    ids compare without regard to case. Refuse a report that:
    - has no LINE lines, or more than MAX_LINES of them;
    - has a LINE that names no source page, or names a page that is not one of `page_ids`;
    - has no NOT READ line;
    - has a NOT READ line that names no pages and does not say one of NONE_WORDS;
    - has a NOT READ line that names a page that is not one of `page_ids`.
    """
    # TODO 1: parse the report; refuse no lines, and more than MAX_LINES.
    # TODO 2: for every line, refuse an empty sources list and any source not in page_ids.
    # TODO 3: refuse a missing NOT READ line.
    # TODO 4: for a NOT READ line with no page ids, read its text: it must be one of NONE_WORDS.
    # TODO 5: refuse any NOT READ page that is not in page_ids.
    raise NotImplementedError("write check_report")
