"""lantern.compaction: the ledger, the check and the three compactors."""

import json

from lantern import compaction
from lantern.testing import Scripted, say

LOWMARSH = {"statement": "lowmarsh-shipping.csv", "holder": "Lowmarsh Shipping Services Ltd",
            "paid_out_to": [{"payee": "Calder Reach Holdings Ltd", "payments": 8,
                             "total": "1873000.00"},
                            {"payee": "Sabran Mercantile Bank", "payments": 3, "total": "135.00"}]}
CORVANE = {"statement": "corvane-trading.csv", "holder": "Corvane Trading Ltd",
           "paid_out_to": [{"payee": "Lowmarsh Shipping Services Ltd", "payments": 9,
                            "total": "2262000.00"}]}
GOOD = {"flows": [
    {"payer": "Corvane Trading Ltd", "payee": "Lowmarsh Shipping Services Ltd", "payments": 9,
     "total": "2262000.00", "source": "corvane-trading.csv"},
    {"payer": "Lowmarsh Shipping Services Ltd", "payee": "Calder Reach Holdings Ltd",
     "payments": 8, "total": "1,873,000.00", "source": "lowmarsh-shipping.csv"}],
    "accounts_read": ["corvane-trading.csv", "lowmarsh-shipping.csv"], "open_questions": []}


def conversation():
    def call(file):
        return {"role": "assistant", "content": "",
                "tool_calls": [{"function": {"name": "money_out", "arguments": {"file": file}}}]}
    return [{"role": "system", "content": "rules"}, {"role": "user", "content": "trace it"},
            call("corvane-trading.csv"), {"role": "tool", "content": json.dumps(CORVANE)},
            call("lowmarsh-shipping.csv"), {"role": "tool", "content": json.dumps(LOWMARSH)}]


def ledger():
    out = {}
    compaction.record(conversation(), out)
    return out


def test_the_ledger_keeps_every_digest_and_leaves_banks_out_of_the_flows():
    flows = compaction.seen_flows(ledger())
    assert [(f["payer"], f["payee"]) for f in flows] == [
        ("Corvane Trading Ltd", "Lowmarsh Shipping Services Ltd"),
        ("Lowmarsh Shipping Services Ltd", "Calder Reach Holdings Ltd")]


def test_a_complete_form_passes_and_commas_in_a_total_do_not_matter():
    assert compaction.check(GOOD, ledger()) == []


def test_the_check_names_what_is_missing_or_wrong():
    no_payer = json.loads(json.dumps(GOOD))
    no_payer["flows"][0]["payer"] = ""
    assert "flow 1 has no payer" in compaction.check(no_payer, ledger())
    wrong = json.loads(json.dumps(GOOD))
    wrong["flows"][1]["total"] = "1837000.00"
    assert any("the tool said 1873000.00" in p for p in compaction.check(wrong, ledger()))
    dropped = {**GOOD, "flows": GOOD["flows"][:1]}
    assert any(p.startswith("missing: Lowmarsh") for p in compaction.check(dropped, ledger()))
    invented = json.loads(json.dumps(GOOD))
    invented["flows"].append({"payer": "Corvane Trading Ltd", "payee": "Arden Logistics Ltd",
                              "payments": 2, "total": "5.00", "source": "corvane-trading.csv"})
    assert any(p.startswith("not in any tool result") for p in
               compaction.check(invented, ledger()))
    unread = {**GOOD, "accounts_read": ["corvane-trading.csv"]}
    assert compaction.check(unread, ledger()) == [
        "accounts_read leaves out lowmarsh-shipping.csv"]


def test_survived_wants_payer_payee_and_total_together():
    flows = compaction.seen_flows(ledger())
    assert compaction.survived("Corvane Trading Ltd paid Lowmarsh Shipping Services Ltd "
                               "2,262,000.00.", flows) == 1
    assert compaction.survived("Payments of 2262000 and 1873000 were seen.", flows) == 0


def test_a_refused_form_is_asked_for_again_and_then_filled_in_by_code():
    bad = json.dumps({**GOOD, "flows": GOOD["flows"][:1]})
    log = compaction.Log()
    chat = Scripted([say(bad), say(bad), say(bad)])
    hook = compaction.with_schema(chat, threshold=1, count=len, log=log, retries=2)
    out = hook(conversation())
    assert (log.compactions, log.refused, chat.calls) == (1, 3, 3)
    assert "refused" in chat.requests[1]["messages"][-1]["content"]
    assert len(out) == 3 and out[2]["content"].startswith(compaction.HEAD)
    assert log.kept == [(2, 2)], "after three refusals the form comes from the ledger"


def test_from_source_needs_no_model_and_keeps_every_flow():
    log = compaction.Log()
    out = compaction.from_source(threshold=1, count=len, log=log)(conversation())
    state = json.loads(out[2]["content"].split("\n", 1)[1].rsplit("\n", 1)[0])
    assert compaction.check(state, ledger()) == [] and log.kept == [(2, 2)]


def test_nothing_is_compacted_under_the_threshold():
    log = compaction.Log()
    messages = conversation()
    assert compaction.from_source(threshold=10**9, count=len, log=log)(messages) == messages
    assert log.compactions == 0


# Regressions from the review of 21 November 2026.

def test_an_invented_flow_to_a_bank_is_refused():
    """A flow to a payee with "Bank" in its name is not required, but it must still be in a
    tool result: an invented one is the poisoning this lab teaches."""
    form = json.loads(json.dumps(GOOD))
    form["flows"].append({"payer": "Corvane Trading Ltd", "payee": "Halden Private Bank",
                          "payments": 1, "total": "296400.00", "source": "corvane-trading.csv"})
    problems = compaction.check(form, ledger())
    assert "not in any tool result: Corvane Trading Ltd paid Halden Private Bank" in problems


def test_a_real_flow_to_a_bank_is_let_through():
    form = json.loads(json.dumps(GOOD))
    form["flows"].append({"payer": "Lowmarsh Shipping Services Ltd",
                          "payee": "Sabran Mercantile Bank", "payments": 3, "total": "135.00",
                          "source": "lowmarsh-shipping.csv"})
    assert compaction.check(form, ledger()) == []


def test_survived_matches_a_total_as_a_whole_figure():
    flow = [{"payer": "Corvane Trading Ltd", "payee": "Lowmarsh Shipping Services Ltd",
             "total": "2262000.00"}]
    text = "Corvane Trading Ltd paid Lowmarsh Shipping Services Ltd "
    assert compaction.survived(text + "22620000.00", flow) == 0
    assert compaction.survived(text + "12262000", flow) == 0
    assert compaction.survived(text + "2,262,000", flow) == 1
    assert compaction.survived(text + "2262000.00.", flow) == 1


def test_a_form_with_figures_that_are_not_strings_is_checked_not_crashed():
    form = json.loads(json.dumps(GOOD))
    form["flows"][0]["total"] = None
    form["flows"][1]["total"] = ["1873000.00"]
    form["flows"][1]["payments"] = {"n": 8}
    problems = compaction.check(form, ledger())
    assert problems[0] == "flow 1 has no total"
    assert any("total ['1873000.00']" in p for p in problems)
    assert compaction.check(["not", "a", "form"], ledger()) == ["the form is not a JSON object"]
    form = json.loads(json.dumps(GOOD))
    form["flows"][0]["total"] = 2262000
    form["flows"][0]["payments"] = "9"
    assert compaction.check(form, ledger()) == []


def test_the_head_is_found_by_role_not_position():
    two_systems = [{"role": "system", "content": "rules"},
                   {"role": "system", "content": "listing"}, *conversation()[1:]]
    head, task = compaction._head(two_systems)
    assert [m["role"] for m in head] == ["system", "system", "user"] and task == "trace it"
    assert "listing" not in compaction._rendered(two_systems)
    no_system = conversation()[1:]
    head, task = compaction._head(no_system)
    assert head == no_system[:1] and "trace it" not in compaction._rendered(no_system)


def test_the_report_check_matches_whole_figures_on_the_flow_line():
    led = ledger()
    covers = compaction.report_covers(led)
    good = ("FLOW: Corvane Trading Ltd -> Lowmarsh Shipping Services Ltd | 9 payments | total "
            "2,262,000.00\nFLOW: Lowmarsh Shipping Services Ltd -> Calder Reach Holdings Ltd | 8 "
            "payments | total 1873000.00\nDONE")
    assert covers(good) is None
    assert covers(good.replace("2,262,000.00", "22,620,000.00")) is not None
