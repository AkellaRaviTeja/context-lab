"""The same rows in six shapes. Chapter 05 counts each in tokens and scores how it is read.

Every function takes a list of flat records (dicts with the same keys, values already strings)
and returns text. None of them changes a value: what differs is how often the keys are written
and what separates the cells.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import yaml

Rows = list[dict[str, str]]


def to_json(rows: Rows) -> str:
    return json.dumps(rows, indent=2)


def to_compact_json(rows: Rows) -> str:
    return json.dumps(rows, separators=(",", ":"))


def to_yaml(rows: Rows) -> str:
    return yaml.safe_dump(rows, sort_keys=False, default_style=None)


def to_markdown(rows: Rows) -> str:
    keys = list(rows[0])
    head = "| " + " | ".join(keys) + " |\n|" + "---|" * len(keys)
    return head + "\n" + "\n".join("| " + " | ".join(r.values()) + " |" for r in rows)


def to_csv(rows: Rows) -> str:
    keys = list(rows[0])
    return ",".join(keys) + "\n" + "\n".join(",".join(_cell(v) for v in r.values()) for r in rows)


def to_toon(rows: Rows, name: str = "rows") -> str:
    """TOON's tabular form: the name, the row count and the keys once, then one line a row."""
    keys = list(rows[0])
    head = f"{name}[{len(rows)}]{{{','.join(keys)}}}:"
    return head + "\n" + "\n".join("  " + ",".join(_cell(v) for v in r.values()) for r in rows)


def _cell(value: str) -> str:
    """A cell for CSV and TOON: quoted only when it holds a comma, a quote or a line break."""
    if any(c in value for c in ',"\n'):
        return '"' + value.replace('"', '""') + '"'
    return value


FORMATS: dict[str, Callable[[Rows], str]] = {
    "JSON, indented": to_json,
    "JSON, compact": to_compact_json,
    "YAML": to_yaml,
    "Markdown table": to_markdown,
    "CSV": to_csv,
    "TOON": to_toon,
}


def render_result(result: dict[str, Any], table: Callable[[Rows], str]) -> str:
    """A tool result with its `lines` drawn as a table and everything else one field a line."""
    if not isinstance(result.get("lines"), list) or not result["lines"]:
        return json.dumps(result)
    head = "\n".join(f"{k}: {v}" for k, v in result.items() if k != "lines")
    rows = [{k: str(v) for k, v in row.items()} for row in result["lines"]]
    return f"{head}\nlines:\n{table(rows)}"
