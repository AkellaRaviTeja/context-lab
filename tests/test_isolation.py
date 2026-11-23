"""lantern.isolation: pages, the reader's report and its check, and what isolation hides."""

from lantern import agent, isolation, trail
from lantern.testing import Scripted, say

GOOD = ("LINE: Corvane Trading Ltd -> Lowmarsh Shipping Services Ltd | 9 payments | total "
        "2,262,000.00 | source: corvane-trading.p1, corvane-trading.p2\nNOT READ: none")
IDS = ["corvane-trading.p1", "corvane-trading.p2", "corvane-trading.p3"]


def test_pages_cover_every_statement_line_once():
    ps = isolation.pages()
    assert len(ps) == 42, len(ps)
    for a in trail.accounts():
        rows = sum(len(p.text.splitlines()) - 2 for p in ps if p.file == a["file"])
        assert rows == len(trail.statement(a["file"])), a["file"]
    assert ps[0].id == "northwind-freight.p1" and ps[0].text.startswith("Page 1 of 5")


def test_a_good_report_passes_and_parses():
    assert isolation.check_report(GOOD, IDS) == []
    lines, not_read = isolation.parse(GOOD)
    assert lines[0]["total"] == 2262000.0 and lines[0]["payments"] == 9
    assert lines[0]["sources"] == ["corvane-trading.p1", "corvane-trading.p2"]
    assert not_read == []


def test_a_report_without_sources_or_not_read_is_refused():
    bare = GOOD.replace(" | source: corvane-trading.p1, corvane-trading.p2", "")
    assert any("no source" in p for p in isolation.check_report(bare, IDS))
    no_list = GOOD.replace("\nNOT READ: none", "")
    assert any("NOT READ" in p for p in isolation.check_report(no_list, IDS))
    blank = GOOD.replace("NOT READ: none", "NOT READ:")
    assert isolation.check_report(blank, IDS)


def test_a_source_that_is_not_the_readers_page_is_refused():
    other = GOOD.replace("corvane-trading.p2", "pellmar-nominees.p1")
    assert any("pellmar-nominees.p1" in p for p in isolation.check_report(other, IDS))
    six = "\n".join([GOOD.splitlines()[0]] * 6) + "\nNOT READ: none"
    assert any("most allowed" in p for p in isolation.check_report(six, IDS))


def test_the_reader_is_sent_back_until_its_report_passes(monkeypatch):
    monkeypatch.setattr(agent.context, "count_tokens", lambda text: len(text.split()))
    model = Scripted([say(calls=[("read_page", {"page": "corvane-trading.p1"})]),
                      say("Corvane paid Lowmarsh."), say(GOOD)])
    rec = isolation.read("corvane-trading.csv", "Who did Corvane pay?", chat=model,
                         limit=100_000)
    assert rec["accepted"] and rec["refused"] == 1 and rec["opened"] == ["corvane-trading.p1"]
    assert model.requests[0]["messages"][1]["content"] == "Who did Corvane pay?"
    assert len(model.requests[0]["messages"]) == 2, "the reader starts with an empty context"


def test_hidden_finds_what_the_main_agent_cannot_see():
    rec = {"file": "corvane-trading.csv", "pages": IDS, "opened": ["corvane-trading.p1"],
           "report": GOOD.replace("2,262,000.00", "2,000,000.00")}
    h = isolation.hidden(rec)
    assert h["wrong_totals"] and not h["wrong_counts"]
    assert h["cited_unopened"] == ["corvane-trading.p2"]
    assert h["unread_not_said"] == ["corvane-trading.p2", "corvane-trading.p3"]
    assert "Arden Logistics Ltd" not in h["left_out"]


def test_follow_up_answers_come_from_the_statements():
    items = {f["id"]: f for f in isolation.follow_ups()}
    assert items["F-1"]["answer"] == "2026-01-27"
    assert isolation.answered("It was 470,000.00 on 2026-02-26.", items["F-3"])
    assert not isolation.answered("It was 470,000.00.", items["F-3"])
    assert not isolation.answered("CAL-00021", items["F-2"])
