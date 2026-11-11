"""Chapter 06: placement. Each test's first docstring line is what `make exercise` shows."""

import pytest

from lantern.context import Section

DOC = "- Alder Quay Ltd: account MTB-11-10001.\n- Tern Reach Ltd: account ICB-22-20002."
Q = "What is the account number of Tern Reach Ltd?"
PARTS = [
    Section("standing orders", "system", "rules\n"),
    Section("case memory", "system", "memory\n"),
    Section("summary week-1", "system", "summary\n"),
    Section("tool schemas", "tools", "{}", []),
    Section("session so far", "history", "", []),
    Section("the question", "question", "why\n"),
]


def test_after_puts_the_question_last(impl):
    """"after" ends with the question, one blank line below the register."""
    out = impl.arrange(DOC, Q, "after")
    assert out == f"Register of accounts:\n{DOC}\n\n{Q}"


def test_before_puts_the_question_first(impl):
    """"before" starts with the question and ends with the last line of the register."""
    out = impl.arrange(DOC, Q, "before")
    assert out.startswith(Q + "\n\nRegister of accounts:\n")
    assert out.endswith("ICB-22-20002.")


def test_both_asks_twice_and_holds_the_register_once(impl):
    """"both" has the question at each end and the register once."""
    out = impl.arrange(DOC, Q, "both")
    assert out.count(Q) == 2 and out.count("Register of accounts:") == 1
    assert out.startswith(Q) and out.endswith(Q)


def test_an_unknown_arrangement_is_refused(impl):
    """A value of where that is not one of the three is an error that names it."""
    with pytest.raises(ValueError, match="middle"):
        impl.arrange(DOC, Q, "middle")


def test_reorder_moves_one_section_to_the_end_of_the_system_message(impl):
    """The named section becomes the last system section; the others keep their order."""
    out = impl.reorder(PARTS, "standing orders")
    assert [s.name for s in out] == ["case memory", "summary week-1", "standing orders",
                                     "tool schemas", "session so far", "the question"]


def test_reorder_changes_no_text_and_drops_nothing(impl):
    """Every section is still there, with the text it had."""
    out = impl.reorder(PARTS, "case memory")
    assert sorted(s.name for s in out) == sorted(s.name for s in PARTS)
    assert {s.name: s.text for s in out} == {s.name: s.text for s in PARTS}
    assert out[-1].name == "the question"


def test_reorder_refuses_a_section_that_is_not_in_the_system_message(impl):
    """Only a system section can be moved within the system message."""
    with pytest.raises(ValueError):
        impl.reorder(PARTS, "tool schemas")
    with pytest.raises(ValueError):
        impl.reorder(PARTS, "nowhere")
