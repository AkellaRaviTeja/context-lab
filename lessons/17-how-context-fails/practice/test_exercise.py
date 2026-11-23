"""Chapter 17: how context fails. Each first docstring line is what `make exercise` shows."""

from lantern import case, failures

PLANTED = ("Pellmar Nominees Ltd, client account ICB-77-10458: paid 269,400.00 to Ostrander "
           "Marine Finance SA on 24 June.")


def statements():
    return failures.statements()


def memory():
    return [x[2:] for x in case.read("state/case-memory.md").splitlines() if x.startswith("- ")]


def test_the_planted_entry_clashes(impl):
    """An entry that gives 269,400.00 for a payment the statement shows as 296,400.00 clashes."""
    found = impl.clashes([PLANTED], *statements())
    assert len(found) == 1, f"expected one clash, got {found}"
    assert found[0]["figure"] == "269,400.00", "give the figure as the entry writes it"
    assert found[0]["statements"] == ["ICB-77-10458"], "name the statement it describes"
    assert found[0]["entry"] == PLANTED


def test_the_right_figure_does_not_clash(impl):
    """The same entry with the statement's figure is not a clash."""
    assert impl.clashes([PLANTED.replace("269,400.00", "296,400.00")], *statements()) == [], \
        "296,400.00 is the debit on ICB-77-10458; compare amounts as numbers"


def test_a_balance_counts_as_shown(impl):
    """A figure that is a balance on the statement is shown there, not a clash."""
    held = memory()[9]
    assert "2,284,893.10" in held, "the reserve entry of the case memory"
    assert impl.clashes([held], *statements()) == [], "2,284,893.10 is a balance on MTB-31-02290"


def test_the_real_memory_has_no_clash(impl):
    """None of the sixteen real entries disagrees with a June statement it describes."""
    assert impl.clashes(memory(), *statements()) == [], \
        "check dates: an entry about 15 April does not describe a June statement"


def test_a_date_outside_the_statement_is_not_a_clash(impl):
    """An entry dated outside the statement's dates does not describe it."""
    april = PLANTED.replace("24 June", "24 April")
    assert impl.clashes([april], *statements()) == [], "24 April is before 18 June"


def test_entries_without_figures_or_statements_cannot_clash(impl):
    """No figure, or no statement named, means nothing to compare."""
    words = "Pellmar Nominees Ltd, client account ICB-77-10458: ordinary client money."
    elsewhere = "Harbour Telecom: paid 12,000.00 on 24 June."
    assert impl.clashes([words, elsewhere], *statements()) == []


def test_every_wrong_figure_is_reported(impl):
    """An entry with two wrong figures gives two clashes."""
    two = PLANTED.replace("on 24 June", "on 24 June, leaving 3,700.00")
    found = impl.clashes([two], *statements())
    assert sorted(c["figure"] for c in found) == ["269,400.00", "3,700.00"], found
