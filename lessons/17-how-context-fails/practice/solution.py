"""Chapter 17 solution: find, in code, a memory entry that disagrees with a statement.

Grade it with `make exercise N=17`. The tests pass in entries as strings and the June
statements from the case, so no model is needed. When it passes, `make lesson N=17 ARGS=--mine`
runs your check on the real case memory and on the copy with the planted entry.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December")
# A figure as entries write it: 296,400.00 or 296400.00.
FIGURE = re.compile(r"(?<![\d.])\d{1,3}(?:,\d{3})*\.\d{2}(?!\d)|(?<![\d.,])\d{4,}\.\d{2}(?!\d)")
# A day as entries write it: 24 June. The year is 2026.
DAY = re.compile(r"\b(\d{1,2}) (" + "|".join(MONTHS) + r")\b")


def clashes(entries: list[str], stmts: dict[str, list[dict[str, str]]],
            holders: dict[str, str]) -> list[dict[str, Any]]:
    """Entries that state a figure a statement they describe does not show.

    `stmts` maps an account number to its rows, in date order; each row has "posted"
    (2026-06-24T14:14:03), "counterparty", "debit", "credit" and "balance" (figures without
    commas, or ""). `holders` maps the same account numbers to their holders.

    - An entry describes a statement when the entry's text contains the account number, the
      holder, or the counterparty of any row, and every date it gives (if any) is within the
      statement's first and last posted dates. (One date inside is enough.)
    - A figure in the entry clashes when it is the amount of no debit, credit or balance on
      any statement the entry describes. Compare amounts as numbers, not as text.
    - Return one dict a clashing figure: {"entry": ..., "figure": <as written in the entry>,
      "statements": [the account numbers the entry describes]}.
    - An entry with no figure, or that describes no statement, cannot clash.
    """
    out = []
    for entry in entries:
        figures = FIGURE.findall(entry)
        if not figures:
            continue
        days = [date(2026, MONTHS.index(m) + 1, int(d)) for d, m in DAY.findall(entry)]
        described = []
        for number, rows in stmts.items():
            names = {number, holders[number]} | {r["counterparty"] for r in rows}
            if not any(n and n in entry for n in names):
                continue
            first = date.fromisoformat(rows[0]["posted"][:10])
            last = date.fromisoformat(rows[-1]["posted"][:10])
            if days and not any(first <= d <= last for d in days):
                continue
            described.append(number)
        if not described:
            continue
        shown = {float(r[k]) for n in described for r in stmts[n]
                 for k in ("debit", "credit", "balance") if r[k]}
        for f in figures:
            if float(f.replace(",", "")) not in shown:
                out.append({"entry": entry, "figure": f, "statements": described})
    return out
