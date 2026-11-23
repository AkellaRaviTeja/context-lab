"""Chapter 21 exercise: a client-side backend for the memory tool (memory_20250818).

With the memory tool the model sends commands on files under /memories and the application
carries them out. Write the six commands so that they are carried out on a lantern.memory
Store: every file is an entry (id "<path>@<n>"), every edit supersedes the version before it,
every write goes through the store's policy (a file with no "Source:" line is held), and
delete retracts.

The paths, versions and replies are done for you below. Grade it with `make exercise N=21`
(offline, no model); then `make lesson N=21 ARGS=--mine` runs the chapter on yours.
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

    # ---- the six commands: yours to write -----------------------------------------------------

    def view(self, raw: str = ROOT, view_range: list[int] | None = None) -> str:
        """A directory: "Files in <path>:" and one line a live file, "<bytes>\t<path>", with
        "\t(held for review)" after a held one, or "(empty)". A file: its lines numbered as
        f"{n:6d}\t{line}", only lines first to last when `view_range` is [first, last]
        (last -1: to the end). A held file: a reply that says it is held and does not show
        its text. A path that is neither: ToolError."""
        # TODO 1: path = self.path(raw); e = self.live(path).
        # TODO 2: no file there: list self.files(path) (ToolError if none and path != ROOT).
        # TODO 3: a held file: say so, without its text. Else number its lines.
        raise NotImplementedError("write view")

    def create(self, raw: str, file_text: str) -> str:
        """A new file, written through the store (its policy decides kept or held); on an
        existing file, a new version that supersedes it. Creating ROOT itself: ToolError.
        Reply with self._said(entry, "File created at <path>.")."""
        # TODO 4: self.store.write(self._entry(path, file_text)), or self._replace(old, ...).
        raise NotImplementedError("write create")

    def str_replace(self, raw: str, old_str: str, new_str: str) -> str:
        """Replace text that occurs exactly once in the live file (ToolError otherwise, saying
        how many times it occurs), as a new version."""
        # TODO 5: count the matches; self._replace(e, new text, "str_replace").
        raise NotImplementedError("write str_replace")

    def insert(self, raw: str, insert_line: int, insert_text: str) -> str:
        """Insert text after line `insert_line` (0: at the top), as a new version. A line
        outside 0 to the number of lines: ToolError."""
        # TODO 6: split into lines, insert, join with "\n", self._replace(...).
        raise NotImplementedError("write insert")

    def delete(self, raw: str) -> str:
        """Take a file, or every file under a directory, out of /memories, and reply
        "Deleted <path>.". on_delete="retract": self.store.retract the live version (its text
        stays, marked). on_delete="forget": self.store.forget every version of the file that
        is not forgotten already. Nothing there: ToolError."""
        # TODO 7: the targets are [self.live(path)] or self.files(path).
        raise NotImplementedError("write delete")

    def rename(self, old_raw: str, new_raw: str) -> str:
        """Move a file: the new path's first version supersedes the old path's last
        (self.store.supersede with self._entry(new_path, text)). The new path taken already:
        ToolError."""
        # TODO 8: check both paths, then supersede.
        raise NotImplementedError("write rename")

    # ---- the audit ------------------------------------------------------------------------------

    def history(self, raw: str) -> list[dict[str, Any]]:
        """Every event in the store's log on any version of a file, oldest first."""
        path = self.path(raw)
        return [e for e in self.store.events() if e["entry"].rpartition("@")[0] == path]
