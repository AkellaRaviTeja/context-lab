"""Chapter 01: the whole input. Each test's first docstring line is what `make exercise` shows."""

import pytest

from lantern import context
from lantern.context import Section

PARTS = [
    Section("orders", "system", "Cite the evidence.\nNever state a currency.\n"),
    Section("memory", "system", "# Memory\n\n- Pellmar: cleared by the FIU.\n- Corvane: owned.\n"),
    Section("summary", "system", "  Pellmar is cleared, so no action.\n  Carried: cleared.\n"),
    Section("question", "question", "Should it have been escalated?\n"),
]


def words(text: str) -> int:
    return len(text.split())


def test_line_numbers_run_on_across_sections(impl):
    """Line numbers count through the whole input, not from the top of each section."""
    found = impl.locate(PARTS, "cleared")
    assert [n for n, _, _ in found] == [5, 7, 8], (
        "number the lines of the flat input: 2 lines of orders, then memory starts at line 3")


def test_line_numbers_start_at_one(impl):
    """The first line of the input is line 1."""
    assert impl.locate(PARTS, "Cite")[0][0] == 1


def test_each_hit_names_its_section_and_the_line(impl):
    """Each hit carries the section it is in and the line, stripped."""
    found = impl.locate(PARTS, "cleared")
    assert found[0][1:] == ("memory", "- Pellmar: cleared by the FIU.")
    assert found[1][1:] == ("summary", "Pellmar is cleared, so no action."), "strip the line"


def test_two_lines_of_one_section_are_two_hits(impl):
    """A phrase on two lines of the same section is found twice."""
    assert [name for _, name, _ in impl.locate(PARTS, "cleared")].count("summary") == 2


def test_nothing_found_is_an_empty_list(impl):
    """A phrase that is nowhere gives an empty list, not an error."""
    assert impl.locate(PARTS, "Ostrander") == []


def test_shares_use_the_counter_they_are_given(impl):
    """Shares are measured with the counter passed in, not by characters."""
    got = impl.shares(PARTS, words)
    total = sum(words(s.text) for s in PARTS)
    assert got["question"] == pytest.approx(5 / total), "size each section with count(text)"
    assert got["orders"] == pytest.approx(7 / total)


def test_shares_add_up_to_one(impl):
    """The shares of all sections add up to 1."""
    assert sum(impl.shares(PARTS, words).values()) == pytest.approx(1.0)


def test_an_empty_input_has_no_shares(impl):
    """When nothing has any size, every share is 0.0 and nothing divides by zero."""
    assert impl.shares(PARTS, lambda text: 0) == {s.name: 0.0 for s in PARTS}


def test_the_word_in_lanterns_own_input(impl):
    """On LANTERN's input of 13 July, "cleared" is on 8 lines in 6 sections, first at line 49."""
    found = impl.locate(context.sections(), "cleared")
    assert len(found) == 8
    assert len({name for _, name, _ in found}) == 6
    assert found[0][:2] == (49, "case memory")
