"""lantern.baseline and lantern.tools: the signed set, the harness and the interval."""

from __future__ import annotations

import pytest

from lantern import baseline, case, context, tools
from lantern.testing import Scripted, say


def test_the_question_set_is_the_file_that_was_signed():
    qs = baseline.questions()
    assert len(qs) == 26 and [q["id"] for q in qs][:2] == ["Q-01", "Q-02"]
    assert {q["slice"] for q in qs} == {"evidence", "memory", "false memory", "not told",
                                         "rules in conflict"}


def test_an_altered_question_set_is_refused(monkeypatch):
    real = case.read

    def altered(name: str) -> str:
        text = real(name)
        return text.replace('"starts": "yes"', '"starts": "no"', 1) if name.endswith(
            "questions.jsonl") else text

    monkeypatch.setattr(case, "read", altered)
    with pytest.raises(ValueError, match="not the file that was signed"):
        baseline.questions()


def test_no_right_answer_rests_on_an_entry_written_under_eow_fin_07():
    history = case.rows("state/case-memory-history.csv")
    theirs = [r["entry"] for r in history if r["account"] == "eow-fin-07"]
    for q in baseline.questions():
        for n in theirs:
            assert f"entry {n} " not in q["source"] + " " and f"entry {n};" not in q["source"]


def test_wilson_is_wide_on_few_questions_and_needs_one():
    low, high = baseline.wilson(17, 26)
    assert round(low, 2) == 0.46 and round(high, 2) == 0.81
    assert baseline.wilson(0, 4)[0] == 0.0 and baseline.wilson(4, 4)[1] == 1.0
    with pytest.raises(ValueError):
        baseline.wilson(0, 0)


def test_changed_names_what_was_fixed_and_what_was_broken():
    before = [{"id": "a", "passed": True}, {"id": "b", "passed": False}, {"id": "c", "passed": 1}]
    after = [{"id": "a", "passed": False}, {"id": "b", "passed": True}, {"id": "c", "passed": 1}]
    assert baseline.changed(before, after) == {"fixed": ["b"], "broken": ["a"]}
    with pytest.raises(ValueError):
        baseline.changed(before, after[:2])


def test_a_tool_that_is_not_connected_fails_and_says_so():
    out = tools.run("lookup_company", {"registered_name": "Ostrander Marine Finance SA"})
    assert out["failed"] is True and "Nothing was checked" in out["error"]


def test_the_statement_tools_answer_from_the_statements():
    assert tools.run("sum_payments", {"account_holder": "MTB-31-02290",
                                      "counterparty": "Corvane"})["total_in"] == "1183369.26"
    assert "error" in tools.run("statement", {"account_no": "HDB-5-118204"})
    assert len(tools.run("statement", {"account_no": "ICB-77-10458"})["lines"]) == 2


def test_score_runs_a_called_tool_and_grades_the_answer_after_it():
    scripted = Scripted([
        say(calls=[("sum_payments", {"account_holder": "MTB-31-02290",
                                    "counterparty": "Corvane"})]),
        say("Corvane Trading Ltd paid 1,183,369.26 into the reserve."),
    ])
    got = baseline.score(context.sections(), chat=scripted, only=["Q-02"])
    assert got[0]["passed"] and got[0]["called"] == ["sum_payments"]
    assert "1183369.26" in str(scripted.last_tool_results())


def test_score_asks_each_question_with_both_statements_in_the_session():
    scripted = Scripted([say("Yes. It should."), say("No.")])
    got = baseline.score(context.sections(), chat=scripted, only=["Q-15", "Q-16"])
    assert [r["passed"] for r in got] == [True, False]
    with pytest.raises(ValueError):
        baseline.score(context.sections(), chat=scripted, only=["Q-99"])
