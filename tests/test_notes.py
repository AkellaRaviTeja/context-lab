"""lantern.notes: a notebook that keeps only what agrees with its source."""

from lantern.notes import Notebook

GOOD = dict(payer="Corvane Trading Ltd", payee="Lowmarsh Shipping Services Ltd", payments=9,
            total="2,262,000.00", source="corvane-trading.csv")


def test_a_note_that_agrees_with_its_source_is_kept_and_survives_a_restart(tmp_path):
    book = Notebook.open(tmp_path / "notes.json")
    assert book.note_flow(**GOOD) == {"kept": True, "flows_noted": 1}
    again = Notebook.open(tmp_path / "notes.json")
    assert again.flows == [{**GOOD, "total": "2262000.00"}]
    assert again.sources() == ["corvane-trading.csv"]
    assert "Corvane Trading Ltd -> Lowmarsh Shipping Services Ltd | 9 payments" in again.text()


def test_a_note_without_a_source_is_refused(tmp_path):
    book = Notebook.open(tmp_path / "notes.json")
    got = book.note_flow(**{**GOOD, "source": ""})
    assert got["kept"] is False and "needs its source" in got["refused"]
    assert book.flows == [] and len(book.refused) == 1


def test_a_note_that_disagrees_with_its_source_is_refused(tmp_path):
    book = Notebook.open(tmp_path / "notes.json")
    assert "gives 2262000.00" in book.note_flow(**{**GOOD, "total": "2243000.00"})["refused"]
    assert "shows 9 payments" in book.note_flow(**{**GOOD, "payments": 10})["refused"]
    assert "shows no payment to" in book.note_flow(
        **{**GOOD, "payee": "Arden Logistics Ltd"})["refused"]
    assert "is the statement of" in book.note_flow(
        **{**GOOD, "source": "lowmarsh-shipping.csv"})["refused"]
    assert "no statement named" in book.note_flow(**{**GOOD, "source": "nowhere.csv"})["refused"]
    assert book.flows == []


def test_noting_the_same_flow_twice_keeps_one(tmp_path):
    book = Notebook.open(tmp_path / "notes.json")
    book.note_flow(**GOOD)
    book.note_flow(**GOOD)
    assert len(book.flows) == 1


def test_questions_are_open_until_closed(tmp_path):
    book = Notebook.open(tmp_path / "notes.json")
    book.note_question(question="Who holds SC-0090-0001?")
    assert "open question 1" in book.text()
    assert book.close_question(id="1", answer="Tidewater Holdings Trust") == {"closed": True}
    assert "open question" not in book.text()
    assert book.close_question(id=9)["closed"] is False
