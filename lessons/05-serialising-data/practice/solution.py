"""Chapter 05 reference solution: the same rows as a Markdown table and as TOON."""

from __future__ import annotations

Rows = list[dict[str, str]]


def cell(value: str) -> str:
    """A cell for TOON: quoted only when it holds a comma, a quote or a line break."""
    if any(c in value for c in ',"\n'):
        return '"' + value.replace('"', '""') + '"'
    return value


def to_markdown(rows: Rows) -> str:
    """A Markdown table: the keys once, a rule, then one line a row."""
    keys = list(rows[0])
    head = "| " + " | ".join(keys) + " |\n|" + "---|" * len(keys)
    return head + "\n" + "\n".join("| " + " | ".join(r.values()) + " |" for r in rows)


def to_toon(rows: Rows, name: str = "rows") -> str:
    """TOON's tabular form: the name, the row count and the keys once, then one line a row."""
    keys = list(rows[0])
    head = f"{name}[{len(rows)}]{{{','.join(keys)}}}:"
    return head + "\n" + "\n".join("  " + ",".join(cell(v) for v in r.values()) for r in rows)
