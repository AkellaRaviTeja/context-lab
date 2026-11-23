"""lantern.production: the context version, the change log, the budget alarm, the nightly audit."""

import json
from dataclasses import replace

import pytest

from lantern import case, context, memory, production
from lantern.budget import Budget
from lantern.memory import Entry

RECORD = case.read("personnel/iyer.md")
LOG = case.jsonl("state/memory-write-log.jsonl")
NIGHT = Entry(id="M-17", text="Pellmar: review closed.", kind="fact",
              inquiry=production.INQUIRY, author="eow-fin-07",
              written_at="2026-08-07T01:58:00", via="svc-lantern-sync")


def store(tmp_path):
    return production.build_store(tmp_path / "m.db", at="2026-08-04T10:00:00", by="a.varma",
                                  reason="FIU note", notes=case.read("state/standing-notes.md"),
                                  inactive={"eow-fin-07": "2026-05-11T09:15:00"})


def test_the_version_covers_the_context_and_not_the_question():
    ps = context.sections()
    v = production.context_version(ps)
    asked = [replace(s, text="Another?\n") if s.where == context.QUESTION else s for s in ps]
    assert production.context_version(asked) == v
    assert production.context_version(context.without(ps, ["DS Iyer"])) != v
    names = [f[0] for f in production.fingerprints(ps)]
    assert "the question" not in names and "standing orders" in names


def test_the_change_log_is_chained_and_shows_an_edit(tmp_path):
    log = production.ChangeLog(tmp_path / "c.jsonl")
    log.add(at="t1", by="a.varma", what="x", reason="r", before="ctx-a", after="ctx-b")
    log.add(at="t2", by="a.varma", what="y", reason="r", before="ctx-b", after="ctx-c")
    assert log.verify() == [] and log.entries()[1]["prev"] == log.entries()[0]["hash"]
    rows = (tmp_path / "c.jsonl").read_text().splitlines()
    first = json.loads(rows[0])
    first["by"] = "o.strand"
    (tmp_path / "c.jsonl").write_text(json.dumps(first) + "\n" + rows[1] + "\n")
    assert log.verify() == ["change 1: altered after it was written"]


def test_the_alarm_warns_before_the_window_is_full():
    plan = Budget(window=1000, reserve=200, limits={"tool schemas": 300})
    assert production.alarm({"a": 500}, plan).level == "ok"
    warn = production.alarm({"a": 500, "b": 150}, plan)
    assert warn.level == "warn" and warn.largest == "a" and "81%" in warn.message
    assert production.alarm({"tool schemas": 301}, plan).level == "over"
    assert production.alarm({"a": 801}, plan).level == "over"


def test_turns_until_counts_whole_turns():
    plan = Budget(window=1000, reserve=200)
    assert production.turns_until(500, 50, plan) == 3  # 640 is 80% of 800: 500, 550, 600, 650
    assert production.turns_until(700, 50, plan) == 0
    with pytest.raises(ValueError):
        production.turns_until(0, 0, plan)


def test_the_store_of_7_august(tmp_path):
    s = store(tmp_path)
    assert {s.get(i).status for i in ("M-08", "M-12", "M-14", "M-16")} == {"retracted"}
    iyer = [e for e in s.visible(production.INQUIRY) if "Iyer" in e.text]
    assert [e.id for e in iyer] == ["N-07"] and iyer[0].author == "l.mensah"
    assert iyer[0].source == "standing note of 2026-06-19"


def test_the_nightly_audit_finds_the_held_write(tmp_path):
    s = store(tmp_path)
    before = production.nightly(s, LOG, RECORD, since="2026-08-05T18:00:00")
    s.write(replace(NIGHT))
    after = production.nightly(s, LOG, RECORD, since="2026-08-06T18:00:00",
                               last_hash=before["last_hash"])
    assert before["ok"] and after["ok"] and after["chain_continues"]
    assert [w["entry"] for w in after["held"]] == ["M-17"]
    assert after["text_matches"] == 16 and after["unsourced_in_log"] == 4


def test_the_nightly_audit_fails_when_the_log_was_rewritten(tmp_path):
    s = store(tmp_path)
    report = production.nightly(s, LOG, RECORD, since="2026-08-05T18:00:00",
                                last_hash="f" * 64)
    assert not report["ok"] and not report["chain_continues"]
    s.db.execute("UPDATE events SET by = 'nobody' WHERE seq = 3")
    assert any("altered" in p for p in production.nightly(s, LOG, RECORD, since="x")["problems"])


def test_a_kept_entry_with_no_source_is_a_problem(tmp_path):
    s = store(tmp_path)
    s.policy = lambda e, st: []
    s.write(replace(NIGHT))
    report = production.nightly(s, LOG, RECORD, since="2026-08-06T18:00:00")
    assert "M-17: kept with no source" in report["problems"]


def test_the_report_and_the_last_hash_are_written(tmp_path):
    s = store(tmp_path)
    report = production.nightly(s, LOG, RECORD, since="2026-08-05T18:00:00")
    out = production.write_report(report, tmp_path / "n", "2026-08-07")
    assert json.loads(out.read_text())["ok"] is True
    assert (tmp_path / "n" / "last-hash").read_text().strip() == report["last_hash"]
    assert memory.GENESIS != report["last_hash"]


def test_the_nightly_job_runs_offline_and_exits_by_its_result(tmp_path, capsys):
    import importlib.util

    path = case.ROOT / "lessons" / "23-context-in-production" / "nightly.py"
    spec = importlib.util.spec_from_file_location("nightly_23", path)
    job = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(job)
    args = ["--store", str(tmp_path / "m.db"), "--out", str(tmp_path / "n"),
            "--since", "2026-08-06T18:00:00", "--day", "2026-08-07"]
    assert job.main(args) == 0 and "0 problems" in capsys.readouterr().out
    (tmp_path / "n" / "last-hash").write_text("0" * 63 + "1\n")
    assert job.main(args) == 1 and "DOES NOT HOLD" in capsys.readouterr().out
