"""The capstone, graded offline. Each test's first docstring line is the behaviour checked.

No model, no network: the agent is given a scripted model (lantern.testing), and the token
counter is a word count.
"""

from __future__ import annotations

import ast
import json
import sqlite3
from pathlib import Path

import pytest

from lantern.testing import Scripted, say

INQ = "EOW/2026/0412"
CLOSED = {"eow-fin-07": "2026-05-11T11:05:00"}


def count(text: str) -> int:
    return len(text.split())


def store(kit, path=":memory:"):
    return kit.memory.MemoryStore(path, closed_accounts=CLOSED)


def fact(s, id, text, **kw):
    base = dict(id=id, text=text, kind="fact", inquiry=INQ, author="d.okafor",
                at="2026-06-19T15:20:00", source="HAL-110952 schedule 1")
    return s.write(**{**base, **kw})


# ---- the store ---------------------------------------------------------------------------------

def test_a_sourced_fact_is_kept_and_an_unsourced_one_is_held(kit):
    """A fact with a source is kept; one with no source and no episode is held, with why."""
    s = store(kit)
    assert fact(s, "M-01", "Pellmar administers Corvane.").status == "kept"
    held = fact(s, "M-08", "Pellmar Nominees: cleared by the FIU.", source=None)
    assert held.status == "held", "an entry with no source must not be kept"
    assert held.problems, "a held entry says why"


def test_machine_writes_and_writes_under_a_closed_account_are_held(kit):
    """The case's four false entries are held twice over: the sync account, the closed login."""
    s = store(kit)
    r = fact(s, "M-08", "Pellmar Nominees: cleared.", author="eow-fin-07",
             at="2026-06-02T01:58:14", via="svc-lantern-sync", source="FIU")
    assert r.status == "held" and len(r.problems) == 2, r.problems


def test_held_entries_are_not_loaded_until_a_person_releases_them(kit):
    """Load reads kept entries only; release names the person and is in the log."""
    s = store(kit)
    fact(s, "M-01", "Pellmar Nominees administers Corvane.", source=None)
    assert s.load(INQ, query="Pellmar") == []
    s.release("M-01", by="a.varma", at="2026-07-14T09:00:00", reason="checked")
    assert [r.id for r in s.load(INQ, query="Pellmar")] == ["M-01"]
    assert s.log()[-1]["by"] == "a.varma"


def test_load_is_scoped_by_inquiry_and_by_officer(kit):
    """Another inquiry's entries and another officer's private notes never load."""
    s = store(kit)
    fact(s, "A", "Pellmar Nominees Ltd holds client money.")
    fact(s, "B", "Pellmar Nominees Ltd: no further action.", inquiry="EOW/2026/0415")
    fact(s, "C", "Pellmar Nominees Ltd: my own note.", user="l.mensah")
    assert [r.id for r in s.load(INQ, query="Pellmar")] == ["A"]
    assert sorted(r.id for r in s.load(INQ, user="l.mensah", query="Pellmar")) == ["A", "C"]


def test_load_ranks_by_relevance_and_respects_k(kit):
    """With a query, the entry about the question comes first, and at most k come back."""
    s = store(kit)
    fact(s, "A", "Northwind Freight banks at Sabran Mercantile Bank.")
    fact(s, "B", "Tidewater's protector is Brightwater and Co.")
    fact(s, "C", "Northwind Freight has no ships and no staff.")
    got = [r.id for r in s.load(INQ, query="Which bank does Northwind use?", k=1)]
    assert got == ["A"], f"expected the bank entry first, got {got}"


def test_retraction_keeps_the_entry_and_names_what_was_built_on_it(kit):
    """Retract returns every summary built on the entry, directly or through another."""
    s = store(kit)
    fact(s, "M-08", "Pellmar is cleared.", source="claimed FIU")
    s.write(id="S-1", text="Week of 15 June.", kind="summary", inquiry=INQ, author="lantern",
            at="2026-06-19T18:00:00", derived_from=["M-08"])
    s.write(id="S-2", text="June.", kind="summary", inquiry=INQ, author="lantern",
            at="2026-06-30T18:00:00", derived_from=["S-1"])
    assert s.retract("M-08", by="a.varma", at="2026-07-20T10:00:00", reason="FIU note") == [
        "S-1", "S-2"]
    assert s.get("M-08").status == "retracted" and s.get("M-08").text
    assert s.load(INQ, query="Pellmar cleared") == [], "a retracted entry is not loaded"


def test_forgetting_erases_the_text_but_not_the_proof(kit):
    """Forget removes what an entry said; the log and the chain still verify."""
    s = store(kit)
    fact(s, "N-7", "DS Iyer is suspended.", kind="procedure")
    s.forget("N-7", by="a.varma", at="2026-08-07T12:30:00", reason="cleared by PS")
    assert s.get("N-7").text == ""
    assert "Iyer" not in json.dumps(s.log()), "the log keeps a hash, not the text"
    assert s.verify() == []


def test_the_chain_catches_an_edited_entry(kit, tmp_path):
    """verify names an entry whose text was changed in the database behind the store."""
    path = str(tmp_path / "m.db")
    s = store(kit, path)
    fact(s, "M-01", "Pellmar administers Corvane.")
    s.db.commit()
    con = sqlite3.connect(path)
    table = [t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    for t in table:
        cols = [c[1] for c in con.execute(f"PRAGMA table_info({t})")]
        for c in cols:
            con.execute(f"UPDATE {t} SET {c} = replace({c}, 'Corvane', 'Arden') "
                        f"WHERE typeof({c}) = 'text' AND {c} NOT LIKE '%\"prev\"%'")
    con.commit()
    assert store(kit, path).verify(), "an edited entry must fail verify"


def test_a_written_id_is_never_overwritten(kit):
    """Writing an id twice is refused: corrections are new entries."""
    s = store(kit)
    fact(s, "M-01", "x")
    with pytest.raises(ValueError):
        fact(s, "M-01", "y")


# ---- the builder -------------------------------------------------------------------------------

def test_stable_sections_go_first_and_the_version_follows_the_text(kit):
    """Stable sections lead, in their order; the same text gives the same version."""
    S = kit.builder.Section
    parts = [S("question", "Is Pellmar cleared?", required=True),
             S("rules", "Cite or say not in evidence.", stable=True, required=True),
             S("tools", "remember(text, source)", stable=True)]
    a = kit.builder.build(parts, budget=100, count=count)
    assert a.order == ["rules", "tools", "question"]
    assert kit.builder.build(parts, budget=100, count=count).version == a.version
    parts[0] = S("question", "Is Ostrander licensed?", required=True)
    b = kit.builder.build(parts, budget=100, count=count)
    assert b.version != a.version and b.stable_version == a.stable_version


def test_over_budget_the_lowest_priority_goes_and_is_named(kit):
    """Over budget, optional sections are dropped lowest priority first, and listed."""
    S = kit.builder.Section
    parts = [S("rules", "r " * 10, stable=True, required=True),
             S("old summaries", "s " * 30, priority=1), S("memory", "m " * 20, priority=5),
             S("question", "q " * 5, required=True)]
    built = kit.builder.build(parts, budget=40, count=count)
    assert built.dropped == ["old summaries"] and built.tokens <= 40
    assert "memory" in built.order


def test_the_rules_and_the_question_are_never_cut(kit):
    """If the required sections alone do not fit, build refuses, it does not truncate."""
    S = kit.builder.Section
    with pytest.raises(kit.builder.OverBudget):
        kit.builder.build([S("rules", "r " * 50, stable=True, required=True),
                           S("question", "q", required=True)], budget=10, count=count)


# ---- the agent ---------------------------------------------------------------------------------

def test_the_agent_answers_from_loaded_memory_with_its_sources_shown(kit):
    """The model sees the loaded entries with their sources, and the answer names them."""
    s = store(kit)
    fact(s, "M-11", "Pellmar Nominees administers Corvane, Osprey Point and Lowmarsh.")
    fact(s, "M-08", "Pellmar Nominees: cleared by the FIU.", source=None)
    model = Scripted([say("Pellmar administers Corvane [M-11].")])
    a = kit.agent.answer("Who does Pellmar Nominees administer?", store=s, inquiry=INQ,
                         chat=model, rules="Cite entry ids.", budget=200, count=count)
    sent = json.dumps(model.requests[0]["messages"])
    assert a.loaded == ["M-11"], "a held entry must not reach the model"
    assert "HAL-110952" in sent and "cleared" not in sent
    assert a.version and a.text.endswith("[M-11].")


def test_a_memory_the_model_proposes_without_a_source_is_held(kit):
    """The model's remember call goes through the store's policy like any other write."""
    s = store(kit)
    model = Scripted([say(calls=[("remember", {"text": "Ostrander is a licensed lender."})]),
                      say("Noted.")])
    a = kit.agent.answer("Anything to remember?", store=s, inquiry=INQ, chat=model,
                         rules="r", budget=200, count=count)
    assert a.proposed and a.proposed[0]["status"] == "held"
    assert s.load(INQ, query="Ostrander") == []
    assert model.calls == 2, "the tool result goes back and the model answers"


def test_the_agent_drops_memory_before_it_cuts_the_question(kit):
    """With a tight budget the memory is dropped and reported; rules and question stay."""
    s = store(kit)
    for i in range(20):
        fact(s, f"F-{i:02d}", f"Pellmar Nominees fact number {i} about the client account.")
    model = Scripted([say("Not in evidence.")])
    a = kit.agent.answer("Pellmar client account?", store=s, inquiry=INQ, chat=model,
                         rules="Answer briefly.", budget=12, count=count)
    assert a.dropped == ["memory"] and a.loaded == []
    assert model.requests[0]["messages"][-1]["content"] == "Pellmar client account?"


# ---- the rule of the capstone ------------------------------------------------------------------

def test_contextkit_imports_nothing_from_lantern_but_the_model_client():
    """Only lantern.llm may be imported (the agent is handed `chat`, so usually not even that)."""
    import os

    root = Path(__file__).resolve().parents[1] / (
        "mine" if os.getenv("CAPSTONE") == "mine" else "solution") / "contextkit"
    assert (root / "__init__.py").exists(), f"{root} does not exist yet"
    bad = []
    for path in root.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            bad += [f"{path.name}: {n}" for n in names
                    if n.split(".")[0] == "lantern" and n not in ("lantern.llm",)]
    assert not bad, f"contextkit must be built from a blank folder: {bad}"
