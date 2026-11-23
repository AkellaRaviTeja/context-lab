"""Chapter 14: the scoped retriever. Each test's first docstring line is what `make exercise`
shows."""

import pytest

from lantern import memory
from lantern.memory import Entry

INQ = "EOW/2026/0412"


def entry(id, text="A line.", **kw):
    base = dict(id=id, text=text, kind="fact", inquiry=INQ, author="d.okafor",
                written_at="2026-06-01T10:00:00", source="bank/accounts.csv")
    return Entry(**{**base, **kw})


def entries():
    return [entry("A", "Pellmar Nominees Ltd administers Corvane.",
                  written_at="2026-04-01T09:00:00"),
            entry("B", "Pellmar Nominees Ltd: reviewed on another inquiry.",
                  inquiry="EOW/2026/0415"),
            entry("C", "Pellmar Nominees Ltd: a private note.", user="l.mensah",
                  written_at="2026-07-01T09:00:00"),
            entry("D", "Pellmar Nominees: cleared by the FIU.", status="held",
                  written_at="2026-06-02T01:58:00"),
            entry("E", "Tidewater's protector is Brightwater.", written_at="2026-05-01T09:00:00")]


def test_held_entries_are_never_loaded(impl):
    """An entry that is not kept is not loaded, whatever the order."""
    for by in ("all", "recency", "relevance"):
        got = [e.id for e in impl.retrieve(entries(), INQ, query="Pellmar cleared", by=by)]
        assert "D" not in got, f"by={by}: a held entry was loaded"


def test_scope_keeps_other_inquiries_and_private_notes_out(impl):
    """With an inquiry, only its shared entries and this officer's own are read."""
    assert [e.id for e in impl.retrieve(entries(), INQ, by="all")] == ["A", "E"], \
        "another inquiry's entry, or another officer's private note, was loaded"
    assert [e.id for e in impl.retrieve(entries(), INQ, user="l.mensah", by="all")] == \
        ["A", "E", "C"], "an officer reads their own private notes, in written order"


def test_no_scope_reads_everything_kept(impl):
    """With inquiry None, every kept entry of every inquiry is a candidate."""
    got = sorted(e.id for e in impl.retrieve(entries(), None, query="Pellmar"))
    assert got == ["A", "B", "C"], f"got {got}"


def test_recency_is_newest_first(impl):
    """by="recency" loads the newest entries first."""
    got = [e.id for e in impl.retrieve(entries(), INQ, user="l.mensah", by="recency", k=2)]
    assert got == ["C", "E"], f"got {got}"


def test_relevance_drops_what_does_not_match(impl):
    """by="relevance" ranks by BM25 and loads nothing that scores zero."""
    got = [e.id for e in impl.retrieve(entries(), INQ, query="Who is Tidewater's protector?")]
    assert got == ["E"], f"got {got}: an entry sharing no word with the question scores 0"


def test_embedding_ranks_by_cosine(impl):
    """by="embedding" ranks by cosine between the query and each entry."""
    def embed(texts, kind):
        if kind == "query":
            return [[1.0, 0.0] for _ in texts]
        return [[0.0, 1.0] if "Tidewater" in t else [0.8, 0.2] for t in texts]

    got = [e.id for e in impl.retrieve(entries(), INQ, query="x", by="embedding", embed=embed)]
    assert got == ["A", "E"], f"got {got}: the entry nearest the query comes first"


def test_k_cuts_after_ordering(impl):
    """k is applied last."""
    got = impl.retrieve(entries(), None, query="Pellmar", k=1)
    assert len(got) == 1, "k=1 loads one entry"


def test_bad_requests_are_refused(impl):
    """A ranked order with no query, embeddings with no model, or an unknown order raise."""
    for kwargs in ({"by": "relevance"}, {"by": "embedding", "query": "x"}, {"by": "random"}):
        with pytest.raises(ValueError):
            impl.retrieve(entries(), INQ, **kwargs)


def test_the_case_store_scoped_loads_no_other_inquiry(impl):
    """On LANTERN's own store, scoped retrieval loads only this inquiry's entries."""
    store = memory.from_case(policy=memory.write_gate())
    got = impl.retrieve(store.all(), INQ, query="Has the FIU cleared Pellmar Nominees?", k=8)
    assert got and all(e.inquiry == INQ for e in got), "another inquiry's entry leaked in"
    assert all(e.status == "kept" for e in got), "a held entry was loaded"
