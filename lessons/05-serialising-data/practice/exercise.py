"""Chapter 05 exercise: the same rows as a Markdown table and as TOON.

Grade it with `make exercise N=05`. The tests pass in rows, so no model is needed. When it
passes, `make lesson N=05 ARGS=--mine` counts and reads the payments in your two shapes.
"""

from __future__ import annotations

Rows = list[dict[str, str]]  # flat records with the same keys; every value is already a string


def cell(value: str) -> str:
    """A cell for TOON: quoted only when it holds a comma, a quote or a line break.

    Inside the quotes a double quote is written twice, as CSV does it.
    """
    # TODO 1: return the value unchanged unless it needs quoting.
    raise NotImplementedError("write cell")


def to_markdown(rows: Rows) -> str:
    """A Markdown table: the keys once, a rule, then one line a row.

    | date | amount |
    |---|---|
    | 2026-01-07 | 86600.00 |
    """
    # TODO 2: the header line, the rule line (one ---| per key), then a line for each row.
    raise NotImplementedError("write to_markdown")


def to_toon(rows: Rows, name: str = "rows") -> str:
    """TOON's tabular form: the name, the row count and the keys once, then one line a row.

    payments[2]{date,amount}:
      2026-01-07,86600.00
      2026-01-09,64000.00
    """
    # TODO 3: the header states len(rows). Each row is two spaces, then its cells joined by
    #         commas, each through cell().
    raise NotImplementedError("write to_toon")
