"""lantern.layout: stable-first order, the Ollama request, cache breakpoints, session prices."""

import pytest

from lantern import context, layout
from lantern.config import load_config


def parts():
    return context.sections()


def changes():
    return {p.name: layout.how_often(p.name) for p in parts()}


def test_today_order_makes_the_request_context_makes():
    assert layout.request(parts()) == context.request(parts())


def test_layout_puts_stable_first_and_the_question_last():
    ordered, ends = layout.layout(parts(), changes())
    names = [p.name for p in ordered]
    assert names[:2] == ["standing orders", "tool schemas"]
    assert names[-3:] == ["case memory", "session so far", "the question"]
    assert len(ends) == 4 and ends[-1] == len(ordered) - 2
    assert [names[i] for i in ends] == ["tool schemas", "summary week-2026-07-06", "case memory",
                                        "session so far"]


def test_layout_refuses_an_unknown_frequency():
    with pytest.raises(ValueError):
        layout.layout(parts(), {**changes(), "case memory": "hourly"})


def test_stable_first_request_moves_memory_out_of_the_system_message():
    ordered, _ = layout.layout(parts(), changes())
    messages, schemas = layout.request(ordered)
    assert messages[0]["role"] == "system"
    assert "# LANTERN case memory" not in messages[0]["content"]
    assert messages[0]["content"].startswith("# LANTERN standing orders")
    assert any(m["role"] == "user" and m["content"].startswith("# LANTERN case memory")
               for m in messages)
    assert messages[-1]["content"] == context.question()
    assert len(schemas) == 19


def test_hosted_request_carries_one_breakpoint_a_group():
    ordered, ends = layout.layout(parts(), changes())
    kwargs = layout.hosted_request(ordered, ends, model="claude-sonnet-5-5", max_tokens=100,
                                   ttl="1h")
    assert layout.breakpoints_in(kwargs) == 4
    assert kwargs["system"][-1]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert "cache_control" not in kwargs, "no automatic caching on top of the breakpoints"
    last = kwargs["messages"][-1]
    assert "cache_control" not in str(last), "the question is never cached"
    with pytest.raises(ValueError):
        layout.hosted_request(ordered, [0, 1, 2, 3, 4], model="m", max_tokens=1)


def test_session_cost_is_a_price_calculation():
    prices = load_config()["hosted"]["prices"]
    none = layout.session_cost(stable=4000, tail=1000, output=100, questions=10, writes=0,
                               prices=prices, cached=False)
    assert none == pytest.approx(10 * (5000 * 2.00 + 100 * 10.00) / 1e6)
    once = layout.session_cost(stable=4000, tail=1000, output=100, questions=10, writes=1,
                               prices=prices)
    every = layout.session_cost(stable=4000, tail=1000, output=100, questions=10, writes=10,
                                prices=prices)
    assert once < none < every
