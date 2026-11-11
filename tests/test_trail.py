"""lantern.trail and lantern.agent: the task, its grader and the loop."""

from lantern import agent, trail
from lantern.testing import Scripted, say


def test_the_trail_is_seven_hops_ending_at_tidewater():
    want = trail.expected()
    assert len(want) == 7
    assert (want[0].payee, want[0].payments, want[0].total) == (
        "Lowmarsh Shipping Services Ltd", 9, 2262000.0)
    assert want[-1].payee == "Tidewater Holdings Trust"
    assert not [f for f in want if f.payee in trail.BANKS or "Northwind" in f.payee]


def test_grade_reads_flow_lines_and_nothing_else():
    report = ("FLOW: Corvane Trading Ltd -> Lowmarsh Shipping Services Ltd | 9 payments | "
              "total 2,262,000.00\n"
              "FLOW: Corvane Trading Ltd -> Sabran Commercial Bank | 3 payments | total 180.00\n"
              "Lowmarsh then paid Calder Reach 1,873,000.00.\nDONE")
    g = trail.grade(report)
    assert (g["found"], g["totals_right"], g["counts_right"], g["invented"]) == (1, 1, 1, 1)
    assert trail.grade("FLOW: Lowmarsh Shipping Services Ltd -> Corvane Trading Ltd | 9 "
                       "payments | total 2262000.00")["found"] == 0, "direction matters"
    assert trail.grade("")["found"] == 0


def test_a_wrong_total_is_found_but_not_right():
    g = trail.grade("FLOW: Osprey Point Management Ltd -> Tidewater Holdings Trust | 8 payments "
                    "| total 1863000.00")
    assert (g["found"], g["totals_right"], g["counts_right"]) == (1, 0, 1)


def test_the_loop_sends_a_report_back_until_the_check_passes(monkeypatch):
    monkeypatch.setattr(agent.context, "count_tokens", lambda text: len(text.split()))
    names = trail.listing(True)[1]
    schemas, handlers, opened = trail.tools(names)
    first = ("FLOW: Corvane Trading Ltd -> Lowmarsh Shipping Services Ltd | 9 payments | "
             "total 1\nDONE")
    chat = Scripted([say(calls=[("money_out", {"file": "corvane-trading.csv"})]), say(first),
                     say(calls=[("money_out", {"file": "lowmarsh-shipping.csv"})]),
                     say("FLOW: none\nDONE")])
    run = agent.run([{"role": "user", "content": "trace"}], chat=chat, schemas=schemas,
                    handlers=handlers, until=trail.not_done(opened))
    assert run.sent_back == 1 and run.stopped == "answered"
    assert opened == ["corvane-trading.csv", "lowmarsh-shipping.csv"]
    assert "Lowmarsh Shipping Services Ltd" in chat.requests[2]["messages"][-1]["content"]


def test_the_loop_stops_before_a_request_that_is_over_the_limit(monkeypatch):
    monkeypatch.setattr(agent.context, "count_tokens", lambda text: len(text.split()))
    chat = Scripted([say("never sent")])
    run = agent.run([{"role": "user", "content": "one two three"}], chat=chat, schemas=[],
                    handlers={}, limit=2)
    assert run.stopped.startswith("over budget before turn 1") and chat.calls == 0
