"""Chapter 18: retract and rebuild. Each test's first docstring line is what `make exercise`
shows."""

from lantern.memory import Entry, Store

INQ = "EOW/2026/0412"
AT = "2026-08-04T10:00:00"


def entry(id, text="A line.", **kw):
    base = dict(id=id, text=text, kind="fact", inquiry=INQ, author="d.okafor",
                written_at="2026-06-01T10:00:00", source="bank/accounts.csv")
    return Entry(**{**base, **kw})


def store():
    s = Store()
    s.write(entry("M-01", written_at="2026-04-23T10:00:00"))
    s.write(entry("M-08", "Pellmar: cleared.", written_at="2026-06-02T01:58:00"))
    s.write(entry("M-14", "Client money.", written_at="2026-06-30T01:58:00"))
    s.write(entry("W-1", "Pellmar is cleared.", kind="summary", source=None, author="lantern",
                  derived_from=["M-01", "M-08"], written_at="2026-06-19T18:00:00"))
    s.write(entry("W-2", "Still cleared.", kind="summary", source=None, author="lantern",
                  derived_from=["W-1", "M-08", "M-14"], written_at="2026-07-03T18:00:00"))
    s.write(entry("X", "Unrelated.", kind="summary", source=None, derived_from=["M-01"],
                  written_at="2026-07-03T19:00:00"))
    return s


def run(impl, s, ids=("M-08",), calls=None):
    calls = [] if calls is None else calls

    def rebuild(old, basis):
        calls.append((old.id, [e.id for e in basis]))
        return f"Rebuilt {old.id} from {len(basis)}."
    return impl.retract_and_rebuild(s, list(ids), by="a.varma", at=AT, reason="FIU note",
                                    rebuild=rebuild)


def test_the_entry_is_retracted_not_deleted(impl):
    """The retracted entry stays in the store, marked, with its text."""
    s = store()
    run(impl, s)
    e = s.get("M-08")
    assert e is not None and e.status == "retracted", "retract it; do not delete it"
    assert e.text == "Pellmar: cleared.", "a retraction keeps the text for the record"


def test_everything_built_on_it_is_rebuilt(impl):
    """Both summaries built on M-08, directly or not, are rebuilt; the unrelated one is not."""
    done = run(impl, store())
    assert done == {"W-1": "W-1-r", "W-2": "W-2-r"}, f"got {done}"


def test_oldest_first_from_the_new_one(impl):
    """A summary built on another summary is rebuilt after it, from the rebuilt one."""
    calls = []
    run(impl, store(), calls=calls)
    assert [c[0] for c in calls] == ["W-1", "W-2"], f"rebuild order: {calls}"
    assert calls[1][1] == ["W-1-r", "M-14"], f"W-2 should rest on W-1-r and M-14: {calls[1]}"


def test_a_retracted_entry_is_never_in_a_basis(impl):
    """What was retracted is left out of what the rebuilt entry rests on."""
    calls = []
    run(impl, store(), ids=("M-08", "M-14"), calls=calls)
    assert calls == [("W-1", ["M-01"]), ("W-2", ["W-1-r"])], f"got {calls}"


def test_rebuilt_entries_supersede_the_old_ones(impl):
    """The old summary is marked superseded and the new one records its basis."""
    s = store()
    run(impl, s)
    assert s.get("W-1").status == "superseded", "supersede the old entry"
    new = s.get("W-1-r")
    assert new.text == "Rebuilt W-1 from 1." and new.derived_from == ["M-01"], new
    assert new.written_at == AT and new.kind == "summary" and new.author == "lantern"


def test_retracting_two_rebuilds_each_once(impl):
    """An entry built on two retracted entries is rebuilt once."""
    calls = []
    done = run(impl, store(), ids=("M-08", "M-14"), calls=calls)
    assert sorted(done) == ["W-1", "W-2"] and len(calls) == 2, f"rebuilt {calls}"


def test_the_chain_still_verifies(impl):
    """After the retraction and the rebuild, the store's own check finds nothing wrong."""
    s = store()
    run(impl, s)
    assert s.verify() == [], s.verify()
