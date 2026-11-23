"""Chapter 20 exercise: the memory audit, every entry joined to where it came from.

Grade it with `make exercise N=20`. The tests run your audit over LANTERN's own store, its write
log and DS Iyer's personnel record, and over small hand-made ones. No model is needed. When it
passes, `make lesson N=20 ARGS=--mine` runs the chapter's audit on yours.
"""

from __future__ import annotations

from typing import Any

from lantern.memory import Store, personnel


def audit(store: Store, write_log: list[dict[str, Any]], record: str) -> list[dict[str, Any]]:
    """One row for every row of the write log, in the log's order, with these keys:

    - "entry": "M-" and the log's entry number, two digits ("M-08");
    - "written_at", "account", "kind", "source", "episode", "host", "session", "tool": as in
      the log; "route": the log's "via";
    - "text_matches": the store has the entry, and its `text_hash` equals the log's
      "text_sha256" (False when the entry is missing from the store);
    - "unsourced": the log gives neither a source nor an episode;
    - "after": when the log's account is the account the personnel record covers, what
      happened (the event text) for every event in the record at or before "written_at",
      oldest first; otherwise an empty list.

    `personnel(record)` (from lantern.memory) returns (account, [(ISO time, what), ...]).
    """
    # TODO 1: read the personnel record's account and events.
    # TODO 2: for each log row, find the entry in the store (store.get).
    # TODO 3: build the row, with text_matches, unsourced and after as described.
    raise NotImplementedError("write audit")
