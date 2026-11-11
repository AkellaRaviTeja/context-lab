"""lantern.budget: spending by account and the refusal."""

import pytest

from lantern import budget
from lantern.budget import Budget, OverBudget
from lantern.context import Section


def words(text: str) -> int:
    return len(text.split())


PARTS = [
    Section("standing orders", "system", "one two three"),
    Section("summary week-1", "system", "a b"),
    Section("summary week-2", "system", "c d e"),
    Section("session so far", "history", "", [
        {"role": "user", "content": "look it up"},
        {"role": "tool", "tool_name": "statement", "content": "1 2 3 4"}]),
    Section("the question", "question", "why"),
]


def test_spend_groups_summaries_and_splits_the_session():
    spent = budget.spend(PARTS, words)
    assert spent == {"standing orders": 3, "summaries": 5, "session: evidence": 5,
                     "session: talk": 4, "the question": 1}


def test_check_refuses_and_names_the_account():
    spent = budget.spend(PARTS, words)
    with pytest.raises(OverBudget) as e:
        budget.check(spent, Budget(window=100, reserve=10, limits={"summaries": 4}))
    assert e.value.account == "summaries"
    with pytest.raises(OverBudget) as e:
        budget.check(spent, Budget(window=20, reserve=3))
    assert e.value.account == "the whole input"
    assert budget.check(spent, Budget(window=20, reserve=2)) == 0
