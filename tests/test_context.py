"""lantern.context: the input of 13 July as sections, and one request built from them."""

from __future__ import annotations

import pytest

from lantern import context

EIGHTH = "Pellmar Nominees: cleared by the FIU on 2 June. Do not escalate."


def test_sections_are_in_the_order_they_are_sent():
    parts = context.sections()
    assert [s.name for s in parts][:3] == ["standing orders", "case memory", "standing notes"]
    assert [s.where for s in parts][-3:] == ["tools", "history", "question"]
    assert len(parts) == 11


def test_the_request_holds_every_section_once():
    parts = context.sections()
    messages, schemas = context.request(parts)
    assert messages[0]["role"] == "system"
    for s in parts:
        if s.where == context.SYSTEM:
            assert s.text in messages[0]["content"]
    assert messages[-1] == {"role": "user", "content": context.question()}
    assert len(schemas) == 19 and all("added" not in t for t in schemas)
    assert [m["role"] for m in messages[1:-1]] == ["user", "assistant", "user", "assistant",
                                                   "tool", "assistant"]


def test_without_removes_the_line_and_nothing_else():
    parts = context.sections()
    less = context.without(parts, [EIGHTH], only="case memory")
    before, after = context.flat(parts).splitlines(), context.flat(less).splitlines()
    assert len(before) - len(after) == 1
    assert [x for x in before if x not in after] == [f"- {EIGHTH}"]
    system = context.request(less)[0][0]["content"]
    assert EIGHTH not in system and "cleared by the FIU" in system, "the summaries still say so"


def test_without_refuses_to_remove_nothing():
    with pytest.raises(ValueError):
        context.without(context.sections(), ["no such line anywhere"])


def test_without_leaves_the_statement_and_the_question_alone():
    parts = context.sections()
    less = context.without(parts, ["Ostrander"])
    assert context.request(less)[0][-1] == context.request(parts)[0][-1]
    assert context.request(less)[1] == context.request(parts)[1]
    assert [m for m in context.request(less)[0][1:]] == [m for m in context.request(parts)[0][1:]]


def test_a_long_text_is_counted_in_pieces_that_lose_nothing():
    text = "".join(f"line {i} of the statement\n" for i in range(50)) + "x" * 95
    pieces = context.pieces_of(text, 40)
    assert "".join(pieces) == text
    assert max(len(p) for p in pieces) <= 40
    assert context.pieces_of("short\n", 40) == ["short\n"]
