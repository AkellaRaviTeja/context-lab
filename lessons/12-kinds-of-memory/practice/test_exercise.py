"""Chapter 12: kinds of memory. Each test's first docstring line is what `make exercise` shows."""

from lantern import memory
from lantern.memory import Entry

INQ = "EOW/2026/0412"


def entry(id, kind="fact", **kw):
    base = dict(id=id, text="A line.", kind=kind, inquiry=INQ, author="d.okafor",
                written_at="2026-06-01T10:00:00", source="bank/accounts.csv")
    return Entry(**{**base, **kw})


def case_memory():
    everything = memory.from_case().all()
    return [e for e in everything if e.inquiry == INQ]


def test_every_kind_is_a_key_in_order(impl):
    """Every kind is a key, in the order of KINDS, empty where there is none."""
    out = impl.by_kind([entry("A")])
    assert list(out) == ["episode", "fact", "procedure", "summary"], "one key per kind, in order"
    assert out["summary"] == [] and out["episode"] == [], "a kind with no entries is an empty list"


def test_the_case_memory_splits_as_the_write_log_says(impl):
    """The sixteen entries split into 3 episodes, 2 procedures and 11 facts."""
    sixteen = sorted((e for e in case_memory() if e.id.startswith("M-")), key=lambda e: e.id)
    out = impl.by_kind(sixteen)
    assert [e.id for e in out["episode"]] == ["M-10", "M-13", "M-15"], "episodes, in order"
    assert [e.id for e in out["procedure"]] == ["M-06", "M-09"], "procedures, in order"
    assert len(out["fact"]) == 11, f"expected 11 facts, got {len(out['fact'])}"


def test_an_unknown_kind_is_refused(impl):
    """An entry of a kind the store does not know raises ValueError."""
    try:
        impl.by_kind([entry("X", kind="rumour")])
    except ValueError as e:
        assert "X" in str(e), "name the entry in the error"
    else:
        raise AssertionError("a kind not in KINDS must raise ValueError")


def test_the_four_unsourced_facts_are_found(impl):
    """In the case memory, M-08, M-12, M-14 and M-16 rest on nothing."""
    got = [e.id for e in impl.unsupported(case_memory())]
    assert got == ["M-08", "M-12", "M-14", "M-16"], f"got {got}"


def test_an_episode_that_is_not_there_supports_nothing(impl):
    """A fact that names an episode missing from the entries is unsupported."""
    entries = [entry("E-1", kind="episode"), entry("F", source=None, episode="E-1"),
               entry("G", source=None, episode="E-9")]
    assert [e.id for e in impl.unsupported(entries)] == ["G"], \
        "E-1 is there and supports F; E-9 is not there and supports nothing"


def test_a_blank_source_is_no_source(impl):
    """A source of only spaces does not count."""
    assert [e.id for e in impl.unsupported([entry("F", source="   ")])] == ["F"], \
        "strip the source before you trust it"


def test_episodes_and_summaries_have_their_own_rule(impl):
    """An episode needs a record; a summary needs what it was built from."""
    entries = [entry("E-1", kind="episode", source=None),
               entry("S-1", kind="summary", source=None, derived_from=["M-01"]),
               entry("S-2", kind="summary", source="weekly run")]
    got = [e.id for e in impl.unsupported(entries)]
    assert got == ["E-1", "S-2"], \
        f"got {got}: an episode with no record, and a summary built from nothing, rest on nothing"


def test_a_procedure_is_checked_like_a_fact(impl):
    """A procedure with neither a record nor an episode is unsupported too."""
    entries = [entry("P", kind="procedure", source=None), entry("Q", kind="procedure")]
    assert [e.id for e in impl.unsupported(entries)] == ["P"], "procedures need support too"
