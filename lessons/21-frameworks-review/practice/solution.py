"""Chapter 21 solution: a client-side backend for the memory tool (memory_20250818).

The model sends commands on files under /memories; this backend carries them out on a
lantern.memory Store, so every file is an entry, every edit supersedes, every write goes
through the store's gate, and delete retracts.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Callable
from datetime import datetime
from typing import Any

from lantern.memory import Entry, Store

ROOT = "/memories"
COMMANDS = ("view", "create", "str_replace", "insert", "delete", "rename")
FIELD = re.compile(r"^(source|episode|kind):[ \t]*(.+?)\s*$", re.I | re.M)


class ToolError(Exception):
    """A command the backend refuses; the model is told why."""


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class MemoryTool:
    """The memory tool's commands, carried out on a Store. Call it with a command's input."""

    def __init__(self, store: Store, *, inquiry: str, author: str = "lantern",
                 via: str = "memory-tool", clock: Callable[[], str] = now,
                 on_delete: str = "retract"):
        if on_delete not in ("retract", "forget"):
            raise ValueError(f"on_delete is 'retract' or 'forget', not {on_delete!r}")
        self.store, self.inquiry, self.author, self.via = store, inquiry, author, via
        self.clock, self.on_delete = clock, on_delete

    def __call__(self, args: dict[str, Any] | None = None, **kwargs: Any) -> str:
        args = {**(args or {}), **kwargs}
        command = args.get("command")
        try:
            if command not in COMMANDS:
                raise ToolError(f"unknown command {command!r}; use one of {', '.join(COMMANDS)}")
            if command == "view":
                return self.view(args.get("path", ROOT), args.get("view_range"))
            if command == "create":
                return self.create(args.get("path", ""), args.get("file_text", ""))
            if command == "str_replace":
                return self.str_replace(args.get("path", ""), args.get("old_str", ""),
                                        args.get("new_str", ""))
            if command == "insert":
                return self.insert(args.get("path", ""), args.get("insert_line", 0),
                                   args.get("insert_text", ""))
            if command == "delete":
                return self.delete(args.get("path", ""))
            return self.rename(args.get("old_path", ""), args.get("new_path", ""))
        except ToolError as e:
            return f"Error: {e}"

    # ---- paths and versions ---------------------------------------------------------------------

    def path(self, raw: Any) -> str:
        """A path under /memories, normalised. Anything that leaves the directory is refused."""
        if not isinstance(raw, str) or not raw.strip():
            raise ToolError("a path is required")
        p = posixpath.normpath(raw.strip())
        if p != ROOT and not p.startswith(ROOT + "/"):
            raise ToolError(f"{raw} is outside {ROOT}")
        return p

    def versions(self, path: str) -> list[Entry]:
        """Every version of a file the store has, oldest first, whatever its status."""
        found = [e for e in self.store.all() if e.id.rpartition("@")[0] == path]
        return sorted(found, key=lambda e: int(e.id.rpartition("@")[2]))

    def live(self, path: str) -> Entry | None:
        """The file as it stands: its latest version, if that is kept or held."""
        v = self.versions(path)
        return v[-1] if v and v[-1].status in ("kept", "held") else None

    def files(self, under: str = ROOT) -> list[Entry]:
        """Every live file under a directory, by path."""
        paths = sorted({e.id.rpartition("@")[0] for e in self.store.all()
                        if e.id.startswith(ROOT + "/") and "@" in e.id})
        prefix = under.rstrip("/") + "/"
        out = [self.live(p) for p in paths if p.startswith(prefix)]
        return [e for e in out if e is not None]

    def _entry(self, path: str, text: str) -> Entry:
        found = {k.lower(): v for k, v in FIELD.findall(text)}
        n = len(self.versions(path)) + 1
        return Entry(id=f"{path}@{n}", text=text, kind=found.get("kind", "fact").lower(),
                     inquiry=self.inquiry, author=self.author, written_at=self.clock(),
                     source=found.get("source"), episode=found.get("episode"), via=self.via)

    def _must(self, path: str) -> Entry:
        e = self.live(path)
        if e is None:
            raise ToolError(f"the path {path} does not exist")
        return e

    def _replace(self, old: Entry, text: str, reason: str) -> Entry:
        path = old.id.rpartition("@")[0]
        return self.store.supersede(old.id, self._entry(path, text), by=self.author,
                                    reason=reason)

    @staticmethod
    def _said(e: Entry, done: str) -> str:
        if e.status == "held":
            return f"{done} It is held for a person's review: {'; '.join(e.problems)}."
        return done

    # ---- the six commands -----------------------------------------------------------------------

    def view(self, raw: str = ROOT, view_range: list[int] | None = None) -> str:
        """A directory: its live files, one a line with its size. A file: its lines, numbered.
        A held file's text is not shown."""
        path = self.path(raw)
        e = self.live(path)
        if e is None:
            listed = self.files(path)
            if not listed and path != ROOT:
                raise ToolError(f"the path {path} does not exist")
            lines = [f"{len(f.text.encode('utf-8'))}\t{f.id.rpartition('@')[0]}"
                     + ("\t(held for review)" if f.status == "held" else "") for f in listed]
            return f"Files in {path}:\n" + ("\n".join(lines) if lines else "(empty)")
        if e.status == "held":
            return (f"{path} is held for a person's review ({'; '.join(e.problems)}). Its text "
                    "is not shown until somebody keeps it.")
        lines = e.text.splitlines()
        first, last = 1, len(lines)
        if view_range:
            first, last = int(view_range[0]), int(view_range[1])
            if last == -1:
                last = len(lines)
            if not 1 <= first <= max(last, 1) or last > len(lines):
                raise ToolError(f"view_range {view_range} is outside the file's "
                                f"{len(lines)} lines")
        return "\n".join(f"{i:6d}\t{lines[i - 1]}" for i in range(first, last + 1))

    def create(self, raw: str, file_text: str) -> str:
        """A new file; on an existing one, a new version that supersedes it."""
        path = self.path(raw)
        if path == ROOT:
            raise ToolError(f"{ROOT} is the directory, not a file")
        old = self.live(path)
        if old is not None:
            e = self._replace(old, file_text, "overwritten by create")
            return self._said(e, f"File {path} overwritten; the earlier version is kept.")
        e = self.store.write(self._entry(path, file_text))
        return self._said(e, f"File created at {path}.")

    def str_replace(self, raw: str, old_str: str, new_str: str) -> str:
        """Replace text that occurs exactly once in the file."""
        path = self.path(raw)
        e = self._must(path)
        n = e.text.count(old_str) if old_str else 0
        if n != 1:
            raise ToolError(f"old_str occurs {n} times in {path}; it must occur exactly once")
        new = self._replace(e, e.text.replace(old_str, new_str, 1), "str_replace")
        return self._said(new, f"File {path} edited.")

    def insert(self, raw: str, insert_line: int, insert_text: str) -> str:
        """Insert text after a line (0: at the top)."""
        path = self.path(raw)
        e = self._must(path)
        lines = e.text.splitlines()
        if not isinstance(insert_line, int) or not 0 <= insert_line <= len(lines):
            raise ToolError(f"insert_line {insert_line} is outside 0 to {len(lines)}")
        lines[insert_line:insert_line] = insert_text.splitlines()
        new = self._replace(e, "\n".join(lines), "insert")
        return self._said(new, f"Text inserted in {path}.")

    def delete(self, raw: str) -> str:
        """Take a file, or every file under a directory, out of /memories. Retracted in the
        store by default (the text stays, marked); with on_delete="forget" every version of it
        is forgotten (the text is erased, the record that it existed stays)."""
        path = self.path(raw)
        targets = [self.live(path)] if self.live(path) else self.files(path)
        if not targets:
            raise ToolError(f"the path {path} does not exist")
        for e in targets:
            if self.on_delete == "forget":  # every version: nothing it said is left to read
                for v in self.versions(e.id.rpartition("@")[0]):
                    if v.status != "forgotten":
                        self.store.forget(v.id, by=self.author, at=self.clock(),
                                          reason="deleted through the memory tool")
            else:
                self.store.retract(e.id, by=self.author, at=self.clock(),
                                   reason="deleted through the memory tool")
        return f"Deleted {path}."

    def rename(self, old_raw: str, new_raw: str) -> str:
        """Move a file. The new path's first version supersedes the old path's last."""
        old_path, new_path = self.path(old_raw), self.path(new_raw)
        e = self._must(old_path)
        if self.live(new_path) is not None:
            raise ToolError(f"{new_path} already exists")
        new = self.store.supersede(e.id, self._entry(new_path, e.text), by=self.author,
                                   reason=f"renamed to {new_path}")
        return self._said(new, f"Renamed {old_path} to {new_path}.")

    # ---- the audit ------------------------------------------------------------------------------

    def history(self, raw: str) -> list[dict[str, Any]]:
        """Every event in the store's log on any version of a file, oldest first."""
        path = self.path(raw)
        return [e for e in self.store.events() if e["entry"].rpartition("@")[0] == path]
