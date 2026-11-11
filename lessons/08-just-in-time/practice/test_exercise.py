"""Chapter 08: just in time. Each test's first docstring line is what `make exercise` shows."""

ACCOUNTS = [
    {"file": "corvane-trading.csv", "holder": "Corvane Trading Ltd",
     "account_no": "SC-0071-5530", "bank": "Sabran Commercial Bank"},
    {"file": "lowmarsh-shipping.csv", "holder": "Lowmarsh Shipping Services Ltd",
     "account_no": "SM-88-410-207", "bank": "Sabran Mercantile Bank"},
    {"file": "calder-reach.csv", "holder": "Calder Reach Holdings Ltd",
     "account_no": "MTB-30-77104", "bank": "Meridian Trust Bank"},
]
LENGTHS = {"corvane-trading.csv": 37, "lowmarsh-shipping.csv": 20, "calder-reach.csv": 19}


def test_a_described_line_says_who_and_where(impl):
    """A described list gives the file, the holder, the account, the bank and the length."""
    text, _ = impl.listing(ACCOUNTS, LENGTHS, described=True)
    lines = text.splitlines()
    assert lines[0] == "Statements on file:"
    assert lines[1] == ("- corvane-trading.csv: Corvane Trading Ltd, SC-0071-5530, "
                        "Sabran Commercial Bank, 37 lines.")
    assert len(lines) == 4


def test_a_described_list_shows_real_names(impl):
    """In a described list the name shown is the real file name."""
    _, names = impl.listing(ACCOUNTS, LENGTHS, described=True)
    assert names == {a["file"]: a["file"] for a in ACCOUNTS}


def test_a_bare_list_tells_the_agent_nothing(impl):
    """A bare list shows numbered names only: no holder, no bank."""
    text, _ = impl.listing(ACCOUNTS, LENGTHS, described=False)
    assert text.splitlines()[1:] == ["- stmt-01.csv", "- stmt-02.csv", "- stmt-03.csv"]
    assert "Corvane" not in text and "Bank" not in text


def test_a_bare_name_still_opens_the_right_file(impl):
    """The map from a bare name leads back to the real file, in the order given."""
    _, names = impl.listing(ACCOUNTS, LENGTHS, described=False)
    assert names == {"stmt-01.csv": "corvane-trading.csv", "stmt-02.csv": "lowmarsh-shipping.csv",
                     "stmt-03.csv": "calder-reach.csv"}


def test_a_payee_with_an_unopened_statement_is_named(impl):
    """A payee whose statement is on file and was not opened is returned."""
    got = impl.unopened(["Lowmarsh Shipping Services Ltd", "Sabran Commercial Bank"], ACCOUNTS,
                        ["corvane-trading.csv"])
    assert got == ["Lowmarsh Shipping Services Ltd"], "a bank has no statement on file"


def test_an_opened_statement_is_not_asked_for_again(impl):
    """Once a payee's statement has been opened it is no longer outstanding."""
    assert impl.unopened(["Lowmarsh Shipping Services Ltd"], ACCOUNTS,
                         ["corvane-trading.csv", "lowmarsh-shipping.csv"]) == []


def test_each_payee_once_whatever_its_case(impl):
    """A payee reported twice is one statement to open, and a holder matches in any case."""
    twice = ["Calder Reach Holdings Ltd", "Calder Reach Holdings Ltd"]
    assert impl.unopened(twice, ACCOUNTS, []) == ["Calder Reach Holdings Ltd"]
    assert impl.unopened(["calder reach holdings ltd"], ACCOUNTS, []) == [
        "calder reach holdings ltd"]
