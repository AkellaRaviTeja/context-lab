"""lantern.memory: kinds, the write policy, scope, retraction, forgetting and the hash chain."""

import sqlite3

import pytest

from lantern import memory
from lantern.memory import Entry, Store

INQ = "EOW/2026/0412"


def entry(id, text="A fact.", **kw):
    base = dict(id=id, text=text, kind="fact", inquiry=INQ, author="d.okafor",
                written_at="2026-06-01T10:00:00", source="bank/accounts.csv")
    return Entry(**{**base, **kw})


def test_an_entry_with_no_source_and_no_episode_is_held_not_kept():
    s = Store()
    kept = s.write(entry("M-1"))
    held = s.write(entry("M-2", source=None))
    assert kept.status == "kept" and held.status == "held"
    assert held.problems == ["no source and no episode"]
    assert [e.id for e in s.visible(INQ)] == ["M-1"], "a held entry is not read"


def test_a_machine_account_and_a_closed_account_are_held_even_with_a_source():
    s = Store(policy=memory.default_policy(inactive={"eow-fin-07": "2026-05-11T11:05:00"}))
    e = s.write(entry("M-1", via="svc-lantern-sync", author="eow-fin-07",
                      written_at="2026-06-02T01:58:14"))
    assert e.status == "held" and len(e.problems) == 2


def test_release_is_a_persons_decision_in_the_log():
    s = Store()
    s.write(entry("M-1", source=None))
    s.release("M-1", by="a.varma", at="2026-07-14T09:00:00", reason="checked against E-02")
    assert s.get("M-1").status == "kept"
    assert s.events()[-1]["by"] == "a.varma"


def test_retracting_names_everything_built_on_it():
    s = Store()
    s.write(entry("M-8"))
    s.write(entry("S-1", kind="summary", derived_from=["M-8"]))
    s.write(entry("S-2", kind="summary", derived_from=["S-1"]))
    s.write(entry("S-3", kind="summary", derived_from=["M-1x"]))
    assert s.retract("M-8", by="a.varma", at="2026-07-20T10:00:00", reason="FIU note") == [
        "S-1", "S-2"]
    assert s.get("M-8").status == "retracted" and s.get("M-8").text, "retracted is not erased"


def test_forgetting_erases_the_text_and_keeps_the_chain_whole():
    s = Store()
    s.write(entry("M-1", text="DS Iyer is a suspect."))
    s.forget("M-1", by="a.varma", at="2026-08-07T16:00:00", reason="cleared")
    assert s.get("M-1").text == "" and s.verify() == []
    assert "Iyer" not in str(s.events())


def test_the_chain_catches_an_edited_entry_and_an_edited_event():
    s = Store()
    s.write(entry("M-1"))
    s.write(entry("M-2"))
    s.db.execute("UPDATE entries SET data = replace(data, 'A fact.', 'Another fact.') "
                 "WHERE id = 'M-2'")
    assert s.verify() == ["M-2: text differs from the text that was written"]
    s.db.execute("UPDATE events SET by = 'someone' WHERE seq = 1")
    assert "event 1: altered after it was written" in s.verify()


def test_scope_keeps_other_inquiries_and_other_officers_private_notes_out():
    s = Store()
    s.write(entry("A", "Pellmar Nominees Ltd: client account reviewed."))
    s.write(entry("B", "Pellmar Nominees Ltd: no further action.", inquiry="EOW/2026/0415"))
    s.write(entry("C", "Pellmar Nominees Ltd: my private note.", user="l.mensah"))
    assert [e.id for e in s.load(INQ, query="Pellmar")] == ["A"]
    assert [e.id for e in s.load(INQ, user="l.mensah", query="Pellmar")] == ["A", "C"]


def test_relevance_ranks_by_bm25_and_recency_by_date():
    s = Store()
    s.write(entry("A", "Northwind Freight banks at Sabran.", written_at="2026-04-01T00:00:00"))
    s.write(entry("B", "Tidewater protector is Brightwater.", written_at="2026-06-01T00:00:00"))
    assert [e.id for e in s.load(INQ, query="Who does Northwind bank with?")] == ["A"]
    assert [e.id for e in s.load(INQ, by="recency")] == ["B", "A"]
    assert len(s.load(INQ, by="all", k=1)) == 1


def test_the_case_memory_replays_with_its_provenance():
    s = memory.from_case()
    eighth = s.get("M-08")
    assert eighth.author == "eow-fin-07" and eighth.via == "svc-lantern-sync"
    assert eighth.source is None and eighth.episode is None
    unsourced = [e.id for e in s.all() if e.id.startswith("M-") and not (e.source or e.episode)]
    assert unsourced == ["M-08", "M-12", "M-14", "M-16"]
    assert s.verify() == []


def test_a_written_id_cannot_be_written_again():
    s = Store()
    s.write(entry("M-1"))
    with pytest.raises(ValueError, match="supersede"):
        s.write(entry("M-1"))


def test_the_store_is_a_file_that_a_new_process_can_open(tmp_path):
    path = tmp_path / "m.db"
    Store(path).write(entry("M-1"))
    assert Store(path).get("M-1").text == "A fact."
    assert sqlite3.connect(path).execute("SELECT count(*) FROM events").fetchone() == (1,)
