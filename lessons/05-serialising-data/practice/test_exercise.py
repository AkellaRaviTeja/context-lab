"""Chapter 05: serialising. Each test's first docstring line is what `make exercise` shows."""

ROWS = [
    {"date": "2026-01-07", "reference": "NW-0365", "amount": "86600.00"},
    {"date": "2026-01-09", "reference": "NW-0370", "amount": "64000.00"},
]


def test_markdown_writes_the_keys_once(impl):
    """A Markdown table names the keys in its first line and nowhere else."""
    out = impl.to_markdown(ROWS).splitlines()
    assert out[0] == "| date | reference | amount |"
    assert out[1] == "|---|---|---|"
    assert out[2] == "| 2026-01-07 | NW-0365 | 86600.00 |"
    assert len(out) == 4 and impl.to_markdown(ROWS).count("amount") == 1


def test_toon_states_the_row_count(impl):
    """TOON's header gives the name, the number of rows and the keys."""
    out = impl.to_toon(ROWS, "payments").splitlines()
    assert out[0] == "payments[2]{date,reference,amount}:"
    assert out[1] == "  2026-01-07,NW-0365,86600.00"
    assert len(out) == 3


def test_toon_counts_the_rows_it_was_given(impl):
    """The count in the header is the number of rows, not a constant."""
    assert impl.to_toon(ROWS * 5).splitlines()[0].startswith("rows[10]{")
    assert impl.to_toon(ROWS[:1], "p").splitlines()[0] == "p[1]{date,reference,amount}:"


def test_a_cell_with_a_comma_is_quoted(impl):
    """A value containing a comma is quoted, or it would read as two cells."""
    rows = [{"payee": "Clarke, Reyes & Co", "amount": "10.00"}]
    assert impl.to_toon(rows).splitlines()[1] == '  "Clarke, Reyes & Co",10.00'
    assert impl.cell("plain") == "plain"


def test_a_quote_inside_a_quoted_cell_is_doubled(impl):
    """A double quote inside a quoted cell is written twice."""
    assert impl.cell('the "loan"') == '"the ""loan"""'


def test_no_value_is_changed(impl):
    """Every value appears in both shapes exactly as it was given."""
    for row in ROWS:
        for v in row.values():
            assert v in impl.to_markdown(ROWS) and v in impl.to_toon(ROWS)


def test_the_real_payments_have_31_rows_in_the_header(impl):
    """On the case's ledger the TOON header says 31."""
    from lantern import case

    rows = case.rows("ledger/halcyon-to-northwind.csv")
    assert impl.to_toon(rows, "payments").splitlines()[0] == (
        "payments[31]{date,payer_account,reference,description,amount}:")
    assert len(impl.to_markdown(rows).splitlines()) == 33
