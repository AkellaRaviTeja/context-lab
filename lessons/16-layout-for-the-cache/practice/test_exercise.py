"""Chapter 16: layout for the cache. Each first docstring line is what `make exercise` shows."""

import pytest

from lantern.context import SYSTEM, Section


def sec(name):
    return Section(name, SYSTEM, name + "\n")


TODAY = [sec("orders"), sec("memory"), sec("notes"), sec("summary"), sec("tools"),
         sec("session"), sec("question")]
CHANGES = {"orders": "rarely", "tools": "rarely", "summary": "weekly", "notes": "weekly",
           "memory": "nightly", "session": "per turn", "question": "per question"}


def names(parts):
    return [p.name for p in parts]


def test_what_changes_least_goes_first(impl):
    """Sections are ordered from the group that changes least to the one that changes most."""
    ordered, _ = impl.layout(TODAY, CHANGES)
    assert names(ordered) == ["orders", "tools", "notes", "summary", "memory", "session",
                              "question"], f"got {names(ordered)}"


def test_ties_keep_their_order(impl):
    """Two sections that change equally often stay in the order they were given."""
    ordered, _ = impl.layout(list(reversed(TODAY)), CHANGES)
    assert names(ordered)[:2] == ["tools", "orders"], "use a stable sort; do not sort by name"
    assert names(ordered)[2:4] == ["summary", "notes"], "ties keep the order they came in"


def test_a_breakpoint_ends_each_group_but_the_last(impl):
    """A breakpoint is the index of the last section of each group, the question's excepted."""
    _, ends = impl.layout(TODAY, CHANGES)
    assert ends == [1, 3, 4, 5], f"expected the ends of rarely, weekly, nightly, per turn: {ends}"


def test_at_most_four_breakpoints(impl):
    """However many groups there are, at most four breakpoints come back."""
    parts = [sec(f"s{i}") for i in range(5)]
    freq = dict(zip(names(parts), impl.CHANGES, strict=True))
    _, ends = impl.layout(parts, freq)
    assert len(ends) <= impl.MAX_BREAKPOINTS, "Anthropic takes at most four"
    assert ends == [0, 1, 2, 3], f"one after each of the first four groups: {ends}"


def test_one_group_needs_no_breakpoint(impl):
    """When everything changes equally often there is nowhere to break."""
    parts = [sec("a"), sec("b")]
    assert impl.layout(parts, {"a": "weekly", "b": "weekly"}) == (parts, [])


def test_an_unknown_frequency_is_an_error(impl):
    """A section with no frequency, or one not in CHANGES, raises ValueError."""
    with pytest.raises(ValueError):
        impl.layout(TODAY, {**CHANGES, "memory": "hourly"})
    with pytest.raises(ValueError):
        impl.layout([*TODAY, sec("new")], CHANGES)


def test_the_list_passed_in_is_not_changed(impl):
    """The caller's list keeps its order."""
    parts = list(TODAY)
    impl.layout(parts, CHANGES)
    assert names(parts) == names(TODAY), "sort a copy, not the list you were given"
