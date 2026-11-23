"""Chapter 20: the memory audit. Each test's first docstring line is what `make exercise`
shows."""

from lantern import case, memory
from lantern.memory import Entry, Store

RECORD = """Account: eow-x

| When | What | Recorded by |
|---|---|---|
| Monday 11 May 2026, 09:15 | Suspended | Supt |
| Monday 11 May 2026, 10:40 | Badge surrendered | a.varma |
"""


def log_row(n, **kw):
    base = {"entry": n, "written_at": "2026-06-02T01:58:00", "account": "eow-x", "kind": "fact",
            "source": None, "episode": None, "via": "svc-sync", "host": "hq-1",
            "session": f"s-{n}", "tool": "memory.append", "text_sha256": memory.sha("A line.")}
    return {**base, **kw}


def small_store():
    s = Store(policy=lambda e, st: [])
    s.write(Entry(id="M-01", text="A line.", kind="fact", inquiry="I", author="eow-x",
                  written_at="2026-06-02T01:58:00"))
    return s


def case_rows(impl):
    return impl.audit(memory.from_case(), case.jsonl("state/memory-write-log.jsonl"),
                      case.read("personnel/iyer.md"))


def test_one_row_per_write_in_order(impl):
    """Every write in the log has a row, in the log's order, named M-01 to M-16."""
    rows = case_rows(impl)
    assert [r["entry"] for r in rows] == [f"M-{i:02d}" for i in range(1, 17)], \
        "one row per log row, entry ids with two digits"


def test_the_route_host_and_session_come_from_the_log(impl):
    """The eighth entry's row names the sync account, its host and its session."""
    m08 = case_rows(impl)[7]
    assert (m08["route"], m08["host"], m08["session"]) == (
        "svc-lantern-sync", "hq-sync-01", "sync-2026-06-02-0158"), m08


def test_unsourced_entries_are_the_four(impl):
    """Exactly M-08, M-12, M-14 and M-16 have neither a source nor an episode."""
    lone = [r["entry"] for r in case_rows(impl) if r["unsourced"]]
    assert lone == ["M-08", "M-12", "M-14", "M-16"], lone


def test_text_is_checked_against_the_logged_hash(impl):
    """Every entry in the case store reads as written; an edited text does not."""
    assert all(r["text_matches"] for r in case_rows(impl)), "the case texts match their hashes"
    rows = impl.audit(small_store(), [log_row(1, text_sha256=memory.sha("Another line."))],
                      RECORD)
    assert rows[0]["text_matches"] is False, "compare the store's text hash with the log's"


def test_a_missing_entry_does_not_match(impl):
    """A write whose entry is no longer in the store is flagged, not skipped."""
    rows = impl.audit(small_store(), [log_row(1), log_row(2)], RECORD)
    assert len(rows) == 2 and rows[1]["text_matches"] is False, rows


def test_after_lists_the_record_events_before_the_write(impl):
    """For the record's account, every event at or before the write, oldest first."""
    rows = impl.audit(small_store(), [log_row(1), log_row(2, written_at="2026-05-11T10:00:00")],
                      RECORD)
    assert rows[0]["after"] == ["Suspended", "Badge surrendered"], rows[0]["after"]
    assert rows[1]["after"] == ["Suspended"], rows[1]["after"]


def test_other_accounts_get_no_events(impl):
    """An officer's entry is not set against somebody else's personnel record."""
    rows = impl.audit(small_store(), [log_row(1, account="d.okafor")], RECORD)
    assert rows[0]["after"] == [], "only the account the record covers"


def test_every_case_entry_with_no_source_came_after_the_badge(impl):
    """In the case, all four unsourced entries follow all five personnel events."""
    lone = [r for r in case_rows(impl) if r["unsourced"]]
    assert all(len(r["after"]) == 5 for r in lone), [r["after"] for r in lone]
