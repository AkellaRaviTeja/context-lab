"""Chapter 03: the budget. Each test's first docstring line is what `make exercise` shows."""

import pytest

SPENT = {"standing orders": 834, "case memory": 508, "tool schemas": 1891, "the question": 71}


def test_a_context_that_fits_returns_what_is_left(impl):
    """A context that fits returns the tokens of input still unspent."""
    b = impl.Budget(window=8192, reserve=400)
    assert impl.check(SPENT, b) == 8192 - 400 - 3304


def test_the_reserve_is_not_for_input(impl):
    """The reserve for the answer is taken off the window before anything is compared."""
    assert impl.check(SPENT, impl.Budget(window=3704, reserve=400)) == 0
    with pytest.raises(impl.OverBudget) as e:
        impl.check(SPENT, impl.Budget(window=3703, reserve=400))
    assert e.value.account == "the whole input"
    assert (e.value.spent, e.value.limit) == (3304, 3303)


def test_an_account_over_its_limit_is_named(impl):
    """An account over its own limit is refused by name, though the whole would fit."""
    b = impl.Budget(window=8192, reserve=400, limits={"tool schemas": 1500})
    with pytest.raises(impl.OverBudget) as e:
        impl.check(SPENT, b)
    assert (e.value.account, e.value.spent, e.value.limit) == ("tool schemas", 1891, 1500)
    assert "391 over" in str(e.value)


def test_exactly_at_a_limit_fits(impl):
    """A limit is the most allowed: an account exactly at its limit fits."""
    b = impl.Budget(window=8192, reserve=400, limits={"standing orders": 834})
    assert impl.check(SPENT, b) > 0


def test_the_first_account_over_is_the_one_named(impl):
    """With two accounts over, the one sent first is named."""
    b = impl.Budget(window=8192, reserve=0, limits={"tool schemas": 10, "case memory": 10})
    with pytest.raises(impl.OverBudget) as e:
        impl.check(SPENT, b)
    assert e.value.account == "case memory"


def test_an_account_is_named_before_the_whole(impl):
    """When an account and the whole are both over, the account is the more useful name."""
    b = impl.Budget(window=1000, reserve=0, limits={"standing orders": 800})
    with pytest.raises(impl.OverBudget) as e:
        impl.check(SPENT, b)
    assert e.value.account == "standing orders"


def test_an_account_with_no_limit_is_only_counted_in_the_whole(impl):
    """An account without a limit of its own is never refused by name."""
    b = impl.Budget(window=8192, reserve=400, limits={"summaries": 5})
    assert impl.check(SPENT, b) == 4488
