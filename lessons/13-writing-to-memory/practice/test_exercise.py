"""Chapter 13: the write gate. Each test's first docstring line is what `make exercise` shows."""

from lantern import memory
from lantern.memory import Entry, Store

INQ = "EOW/2026/0412"
READ = {"ICB-77-10458": "Ostrander Marine Finance SA,HDB-5-120771,296400.00,PNL-CL-0624-1"}
CLOSED = {"eow-fin-07": "2026-05-11T09:15:00"}


def entry(id, text="A line.", **kw):
    base = dict(id=id, text=text, kind="fact", inquiry=INQ, author="d.okafor",
                written_at="2026-06-01T10:00:00", source="bank/accounts.csv")
    return Entry(**{**base, **kw})


def test_the_case_memory_keeps_twelve_and_holds_four(impl):
    """Replayed through the gate, M-08, M-12, M-14 and M-16 are held and the rest kept."""
    s = memory.from_case(policy=impl.write_gate(inactive=CLOSED))
    held = [e.id for e in s.all() if e.status == "held"]
    assert held == ["M-08", "M-12", "M-14", "M-16"], f"held {held}"


def test_the_eighth_fails_on_four_grounds(impl):
    """The eighth has no source, a machine route, a closed account and a judgement."""
    s = memory.from_case(policy=impl.write_gate(inactive=CLOSED))
    problems = s.get("M-08").problems
    assert len(problems) == 4, f"expected four problems, got {problems}"
    assert problems[-1] == "a judgement (cleared): a person must keep it", problems


def test_a_model_entry_its_source_shows_is_kept(impl):
    """LANTERN's line is kept when the statement it cites shows every figure in it."""
    s = Store(policy=impl.write_gate(READ))
    e = s.write(entry("L-1", "Pellmar paid 296,400.00 to HDB-5-120771 (PNL-CL-0624-1).",
                      author="lantern", source="statement ICB-77-10458"))
    assert e.status == "kept", f"a line its source shows should be kept: {e.problems}"


def test_a_figure_the_source_does_not_show_is_held(impl):
    """A figure that is not in the cited statement holds the line."""
    s = Store(policy=impl.write_gate(READ))
    e = s.write(entry("L-1", "Pellmar paid 296,500.00 to HDB-5-120771.", author="lantern",
                      source="ICB-77-10458"))
    assert e.problems == ["the source does not show 296500.00"], e.problems


def test_a_model_must_cite_what_it_read(impl):
    """LANTERN's line that cites nothing read in this session is held."""
    s = Store(policy=impl.write_gate(READ))
    e = s.write(entry("L-1", author="lantern", source="the FIU"))
    assert e.problems == ["cites no document read in this session"], e.problems


def test_an_officer_is_not_checked_against_the_session(impl):
    """The citation check is for the model's own lines, not an officer's."""
    s = Store(policy=impl.write_gate(READ))
    assert s.write(entry("M-1", "Paid 1.00.", source="court order")).status == "kept", \
        "apply the citation check only when the author is one of `models`"


def test_a_planted_judgement_is_held_even_with_a_real_source(impl):
    """A line that says a party is licensed is held, whatever its source."""
    s = Store(policy=impl.write_gate(READ))
    e = s.write(entry("L-1", "Ostrander Marine Finance SA is a licensed lender.",
                      author="lantern", source="ICB-77-10458"))
    assert e.problems == ["a judgement (licensed): a person must keep it"], e.problems


def test_an_open_gate_keeps_everything(impl):
    """With no machine accounts and no closed accounts, only the source and judgement rules hold."""
    s = memory.from_case(policy=impl.write_gate(machine_accounts=()))
    assert [p for p in s.get("M-08").problems] == [
        "no source and no episode", "a judgement (cleared): a person must keep it"], \
        "machine and closed-account problems come only from the settings passed in"


def test_a_document_read_after_the_gate_was_made_counts(impl):
    """The gate sees documents the session reads after it was built."""
    read = {}
    s = Store(policy=impl.write_gate(read))
    read.update(READ)
    e = s.write(entry("L-1", "Paid to HDB-5-120771.", author="lantern", source="ICB-77-10458"))
    assert e.status == "kept", f"keep `read` itself, not a copy of it: {e.problems}"
