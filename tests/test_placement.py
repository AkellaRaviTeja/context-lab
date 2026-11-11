"""lantern.placement: the register and the two ways of moving things."""

import pytest

from lantern import context, placement


def test_the_register_is_the_same_every_time_and_has_no_duplicate_holder():
    rows = placement.register()
    assert rows == placement.register()
    assert len(rows) == 140 and len({name for name, _, _ in rows}) == 140
    name, number, line = rows[80]
    assert line == f"- {name}: account {number}, opened " + line.split("opened ")[1]


def test_no_register_holder_is_in_the_case():
    told = context.flat(context.sections())
    assert not [name for name, _, _ in placement.register() if name in told]


def test_reorder_moves_the_standing_orders_next_to_the_session():
    parts = context.sections()
    moved = placement.reorder(parts, "standing orders")
    system = [s.name for s in moved if s.where == "system"]
    assert system[-1] == "standing orders" and system[0] == "case memory"
    assert sorted(context.flat(moved)) == sorted(context.flat(parts))
    with pytest.raises(ValueError):
        placement.reorder(parts, "session so far")
