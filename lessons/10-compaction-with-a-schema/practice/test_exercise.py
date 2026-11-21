"""Chapter 10: the check. Each test's first docstring line is what `make exercise` shows."""

import copy

LEDGER = {
    "corvane-trading.csv": {"statement": "corvane-trading.csv", "holder": "Corvane Trading Ltd",
                            "paid_out_to": [{"payee": "Lowmarsh Shipping Services Ltd",
                                             "payments": 9, "total": "2262000.00"},
                                            {"payee": "Sabran Commercial Bank", "payments": 3,
                                             "total": "180.00"}]},
    "lowmarsh-shipping.csv": {"statement": "lowmarsh-shipping.csv",
                              "holder": "Lowmarsh Shipping Services Ltd",
                              "paid_out_to": [{"payee": "Calder Reach Holdings Ltd",
                                               "payments": 8, "total": "1873000.00"}]},
}
GOOD = {"flows": [
    {"payer": "Corvane Trading Ltd", "payee": "Lowmarsh Shipping Services Ltd", "payments": 9,
     "total": "2262000.00", "source": "corvane-trading.csv"},
    {"payer": "Lowmarsh Shipping Services Ltd", "payee": "Calder Reach Holdings Ltd",
     "payments": 8, "total": "1873000.00", "source": "lowmarsh-shipping.csv"}],
    "accounts_read": ["corvane-trading.csv", "lowmarsh-shipping.csv"], "open_questions": []}


def changed(**edits):
    state = copy.deepcopy(GOOD)
    for path, value in edits.items():
        i, key = path.split("_", 1)
        state["flows"][int(i[1:])][key] = value
    return state


def test_a_complete_form_is_kept(impl):
    """A form that holds every flow the tools returned, with every field, has no problems."""
    assert impl.check(GOOD, LEDGER) == []


def test_a_line_with_no_payer_is_not_a_line(impl):
    """A flow with an empty field is named by its number and its missing field."""
    problems = impl.check(changed(f0_payer=""), LEDGER)
    assert problems[0] == "flow 1 has no payer"
    assert any(p.startswith("missing: Corvane Trading Ltd paid") for p in problems), (
        "a flow with a missing field does not count as held")


def test_a_dropped_flow_is_named_with_its_source(impl):
    """A flow the tools returned and the form left out is reported with the file it is in."""
    state = {**GOOD, "flows": GOOD["flows"][:1]}
    assert impl.check(state, LEDGER) == [
        "missing: Lowmarsh Shipping Services Ltd paid Calder Reach Holdings Ltd "
        "(lowmarsh-shipping.csv)"]


def test_a_total_is_compared_as_a_number(impl):
    """1,873,000.00 equals 1873000.00, and 1837000.00 does not."""
    assert impl.check(changed(f1_total="1,873,000.00"), LEDGER) == []
    assert impl.check(changed(f1_total="1837000.00"), LEDGER) == [
        "Lowmarsh Shipping Services Ltd paid Calder Reach Holdings Ltd: total 1837000.00, "
        "the tool said 1873000.00"]


def test_a_wrong_count_is_reported(impl):
    """The number of payments must be the tool's."""
    assert impl.check(changed(f0_payments=10), LEDGER) == [
        "Corvane Trading Ltd paid Lowmarsh Shipping Services Ltd: 10 payments, the tool said 9"]


def test_a_flow_no_tool_returned_is_refused(impl):
    """A flow that is in no tool result is reported; a payment to a bank is let through."""
    state = copy.deepcopy(GOOD)
    state["flows"].append({"payer": "Corvane Trading Ltd", "payee": "Arden Logistics Ltd",
                           "payments": 14, "total": "1625000.00",
                           "source": "corvane-trading.csv"})
    state["flows"].append({"payer": "Corvane Trading Ltd", "payee": "Sabran Commercial Bank",
                           "payments": 3, "total": "180.00", "source": "corvane-trading.csv"})
    assert impl.check(state, LEDGER) == [
        "not in any tool result: Corvane Trading Ltd paid Arden Logistics Ltd"]


def test_every_file_opened_must_be_listed(impl):
    """accounts_read must hold every file in the ledger."""
    state = {**GOOD, "accounts_read": ["corvane-trading.csv"]}
    assert impl.check(state, LEDGER) == ["accounts_read leaves out lowmarsh-shipping.csv"]
