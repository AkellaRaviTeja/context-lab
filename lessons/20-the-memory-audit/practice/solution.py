"""Chapter 20 reference solution: the memory audit."""

from __future__ import annotations

from typing import Any

from lantern.memory import Store, personnel


def audit(store: Store, write_log: list[dict[str, Any]], record: str) -> list[dict[str, Any]]:
    """Every write-log row joined to the store and to the personnel record."""
    account, events = personnel(record)
    rows = []
    for r in write_log:
        e = store.get(f"M-{r['entry']:02d}")
        rows.append({
            "entry": f"M-{r['entry']:02d}", "written_at": r["written_at"],
            "account": r["account"], "kind": r["kind"], "source": r["source"],
            "episode": r["episode"], "host": r["host"], "route": r["via"],
            "session": r["session"], "tool": r["tool"],
            "text_matches": e is not None and e.text_hash == r["text_sha256"],
            "unsourced": not (r["source"] or r["episode"]),
            "after": [what for at, what in events if at <= r["written_at"]]
            if r["account"] == account else [],
        })
    return rows
