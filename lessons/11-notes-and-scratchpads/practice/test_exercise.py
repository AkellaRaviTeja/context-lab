"""Chapter 11: the check on a note. Each test's first docstring line is what `make exercise`
shows."""

DIGESTS = {
    "corvane-trading.csv": {
        "statement": "corvane-trading.csv", "holder": "Corvane Trading Ltd",
        "paid_out_to": [{"payee": "Lowmarsh Shipping Services Ltd", "payments": 9,
                         "total": "2262000.00"},
                        {"payee": "Sabran Commercial Bank", "payments": 3, "total": "180.00"}]},
    "lowmarsh-shipping.csv": {
        "statement": "lowmarsh-shipping.csv", "holder": "Lowmarsh Shipping Services Ltd",
        "paid_out_to": [{"payee": "Calder Reach Holdings Ltd", "payments": 8,
                         "total": "1873000.00"}]},
}
GOOD = ("Corvane Trading Ltd", "Lowmarsh Shipping Services Ltd", 9, "2262000.00",
        "corvane-trading.csv")


def digest(file):
    return DIGESTS[file]


def holder_of(file):
    return DIGESTS[file]["holder"] if file in DIGESTS else None


def ask(impl, *note, **edits):
    fields = dict(zip(("payer", "payee", "payments", "total", "source"), note or GOOD,
                      strict=True))
    fields.update(edits)
    return impl.problem_with(*fields.values(), digest=digest, holder_of=holder_of)


def test_a_note_that_agrees_with_its_statement_is_kept(impl):
    """A note that names its statement and agrees with its digest has no problem."""
    assert ask(impl) is None, "a correct note must be kept: return None"
    assert ask(impl, total="2,262,000.00") is None, "a total with commas is the same figure"


def test_a_note_without_a_source_is_refused(impl):
    """A note with no source cannot be checked, so it is not kept."""
    assert ask(impl, source="") == "a note needs its source: the file the flow was read from", (
        "check for an empty source first")


def test_a_statement_that_is_not_on_file_is_refused(impl):
    """A source that names no statement on file is refused, by name."""
    assert ask(impl, source="nowhere.csv") == "no statement named 'nowhere.csv' is on file", (
        "holder_of returns None for a file that is not on file; quote the name with !r")


def test_the_payer_must_hold_the_statement(impl):
    """A flow read from somebody else's statement is refused."""
    assert ask(impl, source="lowmarsh-shipping.csv") == (
        "lowmarsh-shipping.csv is the statement of Lowmarsh Shipping Services Ltd, not of "
        "Corvane Trading Ltd"), "compare holder_of(source) with the payer before the digest"


def test_a_payee_the_statement_never_paid_is_refused(impl):
    """Chapter 09's summary had Corvane paying Arden. The statement shows no such payment."""
    assert ask(impl, payee="Arden Logistics Ltd") == (
        "corvane-trading.csv shows no payment to Arden Logistics Ltd"), (
        "look the payee up in digest(source)['paid_out_to']")


def test_a_total_that_differs_is_refused_as_a_number(impl):
    """2243000.00 is not 2262000.00; the reason quotes both."""
    assert ask(impl, total="2243000.00") == (
        "corvane-trading.csv gives 2262000.00 to Lowmarsh Shipping Services Ltd, the note says "
        "2243000.00"), "compare number(total) with the digest's total"
    assert ask(impl, total=2262000) is None, "a number and a string of the same figure agree"


def test_a_count_that_differs_is_refused(impl):
    """Ten payments where the statement shows nine is a wrong note."""
    assert ask(impl, payments=10) == (
        "corvane-trading.csv shows 9 payments to Lowmarsh Shipping Services Ltd, the note says "
        "10"), "compare the count after the total"
    assert ask(impl, payments="9") is None, '"9" and 9 are the same count'


def test_figures_that_are_not_figures_are_refused_not_crashed(impl):
    """A count of 9.5 or None, or a total of "n/a" or a list, is refused without an error."""
    want = "payments must be a whole number and total a figure"
    for bad in ({"payments": 9.5}, {"payments": None}, {"total": "n/a"},
                {"total": ["2262000.00"]}):
        assert ask(impl, **bad) == want, f"{bad} must be refused with: {want}"
