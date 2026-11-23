"""Chapter 23: the context version. Each test's first docstring line is what `make exercise`
shows."""

import re
from dataclasses import replace

from lantern import context, production


def parts():
    return context.sections()


def swap(ps, name, **kw):
    return [replace(s, **kw) if s.name == name else s for s in ps]


def test_a_version_is_a_short_name(impl):
    """"ctx-" and twelve hex digits."""
    v = impl.context_version(parts())
    assert re.fullmatch(r"ctx-[0-9a-f]{12}", v), f"got {v!r}"


def test_the_same_context_gives_the_same_version(impl):
    """Built twice, the same context has the same version."""
    assert impl.context_version(parts()) == impl.context_version(parts()), \
        "hash a canonical form: json.dumps(..., sort_keys=True)"


def test_one_word_in_the_standing_orders_changes_it(impl):
    """Change one word of the standing orders and the version changes."""
    ps = parts()
    text = next(s.text for s in ps if s.name == "standing orders")
    edited = swap(ps, "standing orders", text=text.replace("Cite", "Quote", 1))
    assert impl.context_version(edited) != impl.context_version(ps)


def test_a_changed_memory_changes_it(impl):
    """Take one line out of the case memory and the version changes."""
    ps = parts()
    assert impl.context_version(context.without(ps, ["Pellmar Nominees: cleared"])) != \
        impl.context_version(ps), "the loaded memory is part of the version"


def test_a_new_question_does_not_change_it(impl):
    """Another question, the same context: the same version."""
    ps = parts()
    other = swap(ps, "the question", text="Who are the directors of Ostrander?\n")
    assert impl.context_version(other) == impl.context_version(ps), \
        "leave the question out of the content"


def test_a_longer_session_does_not_change_it(impl):
    """More turns in the session so far: the same version."""
    ps = parts()
    longer = [replace(s, text=s.text + "user: and?\n", payload=[*s.payload, {
        "role": "user", "content": "and?"}]) if s.where == context.HISTORY else s for s in ps]
    assert impl.context_version(longer) == impl.context_version(ps), \
        "leave the session so far out of the content"


def test_moving_a_section_changes_it(impl):
    """The same sections in another order are another layout, so another version."""
    ps = parts()
    moved = [ps[1], ps[0], *ps[2:]]
    assert impl.context_version(moved) != impl.context_version(ps), "hash the order too"


def test_tool_schemas_are_compared_as_data(impl):
    """A changed tool schema changes it; the same schema with its keys reordered does not."""
    ps = parts()
    tools = next(s for s in ps if s.name == "tool schemas")
    reordered = [dict(reversed(list(t.items()))) for t in tools.payload]
    assert impl.context_version(swap(ps, "tool schemas", payload=reordered)) == \
        impl.context_version(ps), "compare the payload as canonical JSON, not its key order"
    fewer = swap(ps, "tool schemas", payload=tools.payload[1:])
    assert impl.context_version(fewer) != impl.context_version(ps), "the payload is the content"


def test_it_matches_the_lesson(impl):
    """The same version as lantern.production, so --mine records the same names."""
    assert impl.context_version(parts()) == production.context_version(parts())
