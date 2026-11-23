"""Chapter 21: the memory tool's backend. Each test's first docstring line is what
`make exercise` shows."""

from lantern import memory
from lantern.memory import Store

INQ = "EOW/2026/0412"
EIGHTH = memory.from_case().get("M-08").text
SOURCED = "Reserve held under MTB-ORD-0001.\nSource: MTB-ORD-0001"


def tool(impl, **kw):
    ticks = iter(f"2026-08-06T14:{m:02d}:00" for m in range(60))
    return impl.MemoryTool(Store(), inquiry=INQ, clock=lambda: next(ticks), **kw)


def test_create_writes_through_the_gate(impl):
    """A file with a Source: line is kept; the eighth entry's line, with none, is held."""
    t = tool(impl)
    t(command="create", path="/memories/r.md", file_text=SOURCED)
    t(command="create", path="/memories/p.md", file_text=EIGHTH)
    assert t.live("/memories/r.md").status == "kept", "write through self.store.write"
    assert t.live("/memories/p.md").status == "held", "the store's policy decides, not the tool"


def test_view_numbers_the_lines_of_a_file(impl):
    """Viewing a kept file shows its lines numbered, and view_range picks lines."""
    t = tool(impl)
    t(command="create", path="/memories/r.md", file_text=SOURCED)
    assert t(command="view", path="/memories/r.md") == \
        "     1\tReserve held under MTB-ORD-0001.\n     2\tSource: MTB-ORD-0001", \
        'number each line as f"{n:6d}\\t{line}"'
    assert t(command="view", path="/memories/r.md", view_range=[2, 2]) == \
        "     2\tSource: MTB-ORD-0001"


def test_view_does_not_show_a_held_file(impl):
    """A held file's text is not shown back; the directory marks it held."""
    t = tool(impl)
    t(command="create", path="/memories/p.md", file_text=EIGHTH)
    assert "Pellmar" not in t(command="view", path="/memories/p.md"), "hide a held file's text"
    listing = t(command="view", path="/memories")
    assert "/memories/p.md" in listing and "(held for review)" in listing, listing


def test_str_replace_makes_a_new_version(impl):
    """An edit supersedes the old version; both stay in the store."""
    t = tool(impl)
    t(command="create", path="/memories/r.md", file_text=SOURCED)
    t(command="str_replace", path="/memories/r.md", old_str="held", new_str="frozen")
    v = t.versions("/memories/r.md")
    assert [x.status for x in v] == ["superseded", "kept"], [x.status for x in v]
    assert v[-1].text.startswith("Reserve frozen"), v[-1].text


def test_str_replace_needs_one_match(impl):
    """Text that is not in the file, or is in it twice, is an error for the model."""
    t = tool(impl)
    t(command="create", path="/memories/r.md", file_text="a a\nSource: x")
    for old in ("a", "zz"):
        said = t(command="str_replace", path="/memories/r.md", old_str=old, new_str="b")
        assert said.startswith("Error"), f"{old!r}: raise ToolError, got {said!r}"


def test_insert_puts_text_after_a_line(impl):
    """insert_line 1 puts the text after the first line."""
    t = tool(impl)
    t(command="create", path="/memories/r.md", file_text=SOURCED)
    t(command="insert", path="/memories/r.md", insert_line=1, insert_text="Episode: E-07")
    e = t.live("/memories/r.md")
    assert e.text.splitlines()[1] == "Episode: E-07" and e.episode == "E-07", e.text


def test_delete_retracts_and_keeps_the_text(impl):
    """Deleted from /memories, still in the store, marked retracted, with its words."""
    t = tool(impl)
    t(command="create", path="/memories/p.md", file_text=EIGHTH)
    t(command="delete", path="/memories/p.md")
    assert t.live("/memories/p.md") is None, "the file is gone from /memories"
    v = t.versions("/memories/p.md")
    assert v[0].status == "retracted" and v[0].text == EIGHTH, "retract it; do not erase"


def test_delete_as_forget_erases_every_version(impl):
    """With on_delete="forget", no version of the file keeps its text."""
    t = tool(impl, on_delete="forget")
    t(command="create", path="/memories/r.md", file_text=SOURCED)
    t(command="str_replace", path="/memories/r.md", old_str="held", new_str="frozen")
    t(command="delete", path="/memories/r.md")
    assert all(v.text == "" for v in t.versions("/memories/r.md")), "forget every version"
    assert not t.store.verify(), "forget keeps the chain intact"


def test_rename_moves_and_refuses_to_overwrite(impl):
    """A file can move to a free path, not onto another file."""
    t = tool(impl)
    t(command="create", path="/memories/a.md", file_text=SOURCED)
    t(command="create", path="/memories/b.md", file_text=SOURCED)
    said = t(command="rename", old_path="/memories/a.md", new_path="/memories/b.md")
    assert said.startswith("Error"), "the new path is taken"
    t(command="rename", old_path="/memories/a.md", new_path="/memories/c.md")
    assert t.live("/memories/a.md") is None and t.live("/memories/c.md") is not None


def test_every_change_is_in_the_log(impl):
    """The store's chain names the author for every command that changed a file."""
    t = tool(impl)
    t(command="create", path="/memories/r.md", file_text=SOURCED)
    t(command="rename", old_path="/memories/r.md", new_path="/memories/s.md")
    t(command="delete", path="/memories/s.md")
    events = [e["event"] for e in t.store.events()]
    assert events == ["write", "write", "supersede", "retract"], events
    assert {e["by"] for e in t.store.events()} == {"lantern"} and not t.store.verify()
