"""lantern.formats: six shapes, the same values."""

import csv
import io
import json

import yaml

from lantern import case, formats

ROWS = case.rows("ledger/halcyon-to-northwind.csv")


def test_the_ledger_is_the_31_payments_of_case_file_02():
    assert len(ROWS) == 31
    assert list(ROWS[0]) == ["date", "payer_account", "reference", "description", "amount"]
    assert f"{sum(float(r['amount']) for r in ROWS):.2f}" == "2400000.00"


def test_every_shape_holds_the_same_values():
    assert json.loads(formats.to_json(ROWS)) == ROWS
    assert json.loads(formats.to_compact_json(ROWS)) == ROWS
    loaded = yaml.safe_load(formats.to_yaml(ROWS))
    assert [str(r["reference"]) for r in loaded] == [r["reference"] for r in ROWS]
    assert [str(r["amount"]) for r in loaded] == [r["amount"] for r in ROWS]
    assert list(csv.DictReader(io.StringIO(formats.to_csv(ROWS)))) == ROWS
    toon = formats.to_toon(ROWS, "payments").splitlines()
    assert toon[0] == "payments[31]{date,payer_account,reference,description,amount}:"
    assert [line.strip().split(",") for line in toon[1:]] == [list(r.values()) for r in ROWS]
    assert len(formats.to_markdown(ROWS).splitlines()) == 33


def test_a_cell_with_a_comma_is_quoted():
    rows = [{"payee": "Clarke, Reyes & Co", "note": 'the "loan"'}]
    assert formats.to_csv(rows).splitlines()[1] == '"Clarke, Reyes & Co","the ""loan"""'


def test_a_tool_result_keeps_its_fields_and_redraws_its_lines():
    result = {"account_no": "X-1", "balance": "3.00",
              "lines": [{"posted": "2026-06-24", "debit": 5}]}
    out = formats.render_result(result, formats.to_csv)
    assert out == "account_no: X-1\nbalance: 3.00\nlines:\nposted,debit\n2026-06-24,5"
    assert json.loads(formats.render_result({"failed": True}, formats.to_csv)) == {"failed": True}
