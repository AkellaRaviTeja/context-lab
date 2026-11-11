"""Chapter 09: tool results. Each test's first docstring line is what `make exercise` shows."""

import copy

LONG = "date,counterparty,debit\n" + "2026-01-09,Lowmarsh Shipping Services Ltd,250000.00\n" * 12


def call(name, **arguments):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"function": {"name": name, "arguments": arguments}}]}


def tool(content):
    return {"role": "tool", "tool_name": "statement", "content": content}


def conversation():
    return [{"role": "system", "content": "rules"}, {"role": "user", "content": "trace it"},
            call("statement", file="corvane-trading.csv"), tool(LONG),
            call("statement", file="lowmarsh-shipping.csv"), tool(LONG + "second"),
            call("statement", file="calder-reach.csv"), tool(LONG + "third")]


def test_an_old_result_is_replaced_by_a_note(impl):
    """A used result becomes one line that starts by saying it was cleared."""
    out = impl.clear_old(conversation())
    assert out[3]["content"].startswith(impl.CLEARED)
    assert out[5]["content"].startswith(impl.CLEARED)
    assert len(out[3]["content"]) < len(LONG) / 2


def test_the_newest_result_is_kept(impl):
    """The newest tool result is left whole: the agent has not read it yet."""
    assert impl.clear_old(conversation())[7]["content"] == LONG + "third"


def test_the_note_names_the_call(impl):
    """The note says which call the result came from, so it can be made again."""
    out = impl.clear_old(conversation())
    assert "statement(corvane-trading.csv)" in out[3]["content"]
    assert "statement(lowmarsh-shipping.csv)" in out[5]["content"]


def test_a_short_result_is_left_alone(impl):
    """A result too short to be worth clearing stays as it is."""
    messages = conversation()
    messages[3] = tool('{"failed": true, "error": "No file named x."}')
    assert impl.clear_old(messages)[3]["content"] == messages[3]["content"]


def test_clearing_twice_changes_nothing_more(impl):
    """A result already cleared is not cleared again."""
    once = impl.clear_old(conversation())
    assert impl.clear_old(once) == once


def test_nothing_is_added_dropped_or_changed_in_place(impl):
    """The conversation keeps its length and order, and the list passed in is untouched."""
    messages = conversation()
    before = copy.deepcopy(messages)
    out = impl.clear_old(messages)
    assert messages == before, "return new messages; do not edit the ones passed in"
    assert [m["role"] for m in out] == [m["role"] for m in before]
    assert out[2] == before[2] and out[0] == before[0]


def test_a_conversation_with_no_results_is_returned_as_it_is(impl):
    """With no tool results there is nothing to clear."""
    messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "hello"}]
    assert impl.clear_old(messages) == messages
