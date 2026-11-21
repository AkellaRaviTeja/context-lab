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


def test_by_kind_splits_the_case_memory_into_its_kinds():
    sixteen = [e for e in memory.from_case().all() if e.id.startswith("M-")]
    kinds = memory.by_kind(sixteen)
    assert list(kinds) == list(memory.KINDS)
    assert [e.id for e in kinds["episode"]] == ["M-10", "M-13", "M-15"]
    assert [e.id for e in kinds["procedure"]] == ["M-06", "M-09"]
    assert len(kinds["fact"]) == 11 and kinds["summary"] == []
    with pytest.raises(ValueError, match="unknown kind"):
        memory.by_kind([entry("X", kind="rumour")])


def test_unsupported_names_the_four_facts_with_nothing_behind_them():
    everything = memory.from_case().all()
    case = [e for e in everything if e.inquiry == INQ]
    assert [e.id for e in memory.unsupported(case)] == ["M-08", "M-12", "M-14", "M-16"]
    lonely = [entry("F", source=None, episode="E-01"), entry("G", source="  ")]
    assert [e.id for e in memory.unsupported(lonely)] == ["F", "G"], \
        "an episode that is not there, or a blank source, supports nothing"


def test_the_write_gate_holds_the_four_and_keeps_the_twelve():
    gate = memory.write_gate(inactive={"eow-fin-07": "2026-05-11T09:15:00"})
    s = memory.from_case(policy=gate)
    held = [e.id for e in s.all() if e.status == "held"]
    assert held == ["M-08", "M-12", "M-14", "M-16"]
    assert len(s.get("M-08").problems) == 4


def test_the_write_gate_checks_what_the_model_cites():
    read = {"ICB-77-10458": "Ostrander Marine Finance SA,HDB-5-120771,296400.00"}
    s = Store(policy=memory.write_gate(read))
    ok = s.write(entry("L-1", "Pellmar's client account paid 296,400.00 to HDB-5-120771.",
                       author="lantern", source="statement ICB-77-10458"))
    wrong = s.write(entry("L-2", "It paid 296,500.00.", author="lantern",
                          source="statement ICB-77-10458"))
    unread = s.write(entry("L-3", "A line.", author="lantern", source="MTB-31-02290"))
    planted = s.write(entry("L-4", "Ostrander Marine Finance SA is a licensed lender.",
                            author="lantern", source="ICB-77-10458"))
    assert ok.status == "kept", ok.problems
    assert wrong.problems == ["the source does not show 296500.00"]
    assert unread.problems == ["cites no document read in this session"]
    assert planted.problems == ["a judgement (licensed): a person must keep it"]


def test_retrieve_scopes_before_it_ranks_and_reads_only_kept_entries():
    es = [entry("A", "Pellmar Nominees Ltd: reviewed.", written_at="2026-04-01T00:00:00"),
          entry("B", "Pellmar Nominees Ltd: no action.", inquiry="EOW/2026/0415"),
          entry("C", "Pellmar Nominees Ltd: mine.", user="l.mensah"),
          entry("D", "Pellmar Nominees Ltd: held.", status="held")]
    assert [e.id for e in memory.retrieve(es, INQ, query="Pellmar")] == ["A"]
    assert sorted(e.id for e in memory.retrieve(es, None, query="Pellmar")) == ["A", "B", "C"]
    assert [e.id for e in memory.retrieve(es, INQ, by="recency", user="l.mensah")] == ["C", "A"]


def test_retrieve_by_embedding_ranks_by_cosine():
    vectors = {"north": [1.0, 0.0], "tide": [0.0, 1.0], "q": [0.9, 0.1]}

    def embed(texts, kind):
        return [vectors["q"] if kind == "query" else vectors[t.split()[0]] for t in texts]

    es = [entry("A", "tide protector"), entry("B", "north bank")]
    assert [e.id for e in memory.retrieve(es, INQ, query="x", by="embedding", embed=embed,
                                          k=1)] == ["B"]
    with pytest.raises(ValueError):
        memory.retrieve(es, INQ, query="x", by="embedding")


def test_a_deleted_row_is_not_caught_by_verify_but_is_by_vanished():
    s = Store()
    s.write(entry("M-1"))
    s.write(entry("M-2"))
    s.db.execute("DELETE FROM entries WHERE id = 'M-2'")
    assert s.verify() == [] and memory.vanished(s) == ["M-2"]


def test_retract_and_rebuild_rebuilds_summaries_in_order_from_what_is_left():
    s = Store()
    s.write(entry("M-1", written_at="2026-05-01T00:00:00"))
    s.write(entry("M-8", written_at="2026-06-02T00:00:00"))
    s.write(entry("W-1", "Pellmar is cleared.", kind="summary", derived_from=["M-1", "M-8"],
                  written_at="2026-06-19T18:00:00"))
    s.write(entry("W-2", "Still cleared.", kind="summary", derived_from=["W-1", "M-8"],
                  written_at="2026-06-26T18:00:00"))
    seen = []

    def rebuild(old, basis):
        seen.append((old.id, [e.id for e in basis]))
        return f"rebuilt {old.id}"

    done = memory.retract_and_rebuild(s, ["M-8"], by="a.varma", at="2026-08-04T10:00:00",
                                      reason="FIU note", rebuild=rebuild)
    assert done == {"W-1": "W-1-r", "W-2": "W-2-r"}
    assert seen == [("W-1", ["M-1"]), ("W-2", ["W-1-r"])]
    assert s.get("W-1").status == "superseded" and s.get("W-2-r").derived_from == ["W-1-r"]
    assert s.verify() == []


def test_the_audit_joins_every_entry_to_its_route_and_the_personnel_record():
    from lantern import case

    log = case.jsonl("state/memory-write-log.jsonl")
    rows = memory.audit(memory.from_case(), log, case.read("personnel/iyer.md"))
    assert len(rows) == 16 and all(r["text_matches"] for r in rows)
    lone = [r for r in rows if r["unsourced"]]
    assert [r["entry"] for r in lone] == ["M-08", "M-12", "M-14", "M-16"]
    assert {(r["route"], r["host"]) for r in lone} == {("svc-lantern-sync", "hq-sync-01")}
    assert all(len(r["after"]) == 5 for r in lone), "every one after the badge and the revocation"
    assert memory.personnel(case.read("personnel/iyer.md"))[1][1][0] == "2026-05-11T09:15:00"


def test_whole_figure_is_not_fooled_by_a_longer_or_shorter_number():
    assert memory.whole_figure("Held: 2,284,893.10.", "2,284,893.10")
    assert memory.whole_figure("held 2284893.10 in all", "2,284,893.10")
    for wrong in ("12,284,893.10", "2,284,893.1", "2,284,893.105", "2,284,893.11"):
        assert not memory.whole_figure(f"Held: {wrong}.", "2,284,893.10"), wrong


def test_cites_needs_the_exact_id():
    assert memory.cites("Brightwater & Co [M-01].", "M-01")
    for wrong in ("[M-010]", "[M-1]", "M-01-r", "XM-01"):
        assert not memory.cites(f"Brightwater {wrong}", "M-01"), wrong


def test_abstains_in_several_phrasings_and_not_when_it_answers_anyway():
    q = "What is the balance of HDB-5-118204?"
    for ok in ("Not in evidence.", "The case memory does not say.",
               "There is no record of that account's balance (HDB-5-118204).",
               "I was not told; no statement is held."):
        assert memory.abstains(ok, q), ok
    for bad in ("The balance is 40,000.00.", "Not in evidence, but it was 40,000.00.",
                "It was 40,000.00. There is no record of later movements.", ""):
        assert not memory.abstains(bad, q), bad


def test_denies_is_not_fooled_by_not_cleared_or_by_a_yes():
    for ok in ("No. The FIU cleared nothing.", "Pellmar has not been cleared.",
               "There is no record that Pellmar was ever cleared.", "Not in evidence.",
               "The FIU did not clear Pellmar; it never issued a clearance."):
        assert memory.denies(ok, "clear"), ok
    for bad in ("Yes, cleared on 2 June.", "Pellmar Nominees was cleared by the FIU.",
                "It is cleared, not escalated.", "Cleared. Do not escalate.", ""):
        assert not memory.denies(bad, "clear"), bad
