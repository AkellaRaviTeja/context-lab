"""Chapter 23 exercise: the context version, recorded with every answer.

Write `context_version`: one short name for everything LANTERN is given before a question,
so that an answer can be traced to the exact context that produced it. The tests build
contexts from `lantern.context.sections()` (the case files only; no model) and change one thing
at a time. When they pass, `make lesson N=23 ARGS=--mine` versions the chapter's answers with
yours.
"""

from __future__ import annotations

import hashlib
import json

from lantern.context import HISTORY, QUESTION, Section

SESSION_PARTS = (HISTORY, QUESTION)


def content(s: Section) -> str:
    """What a section contributes: a payload sent as JSON (the tool schemas) as canonical JSON,
    so the order of keys is not a change; any other section, its text."""
    if s.payload is not None and s.where not in SESSION_PARTS:
        return json.dumps(s.payload, sort_keys=True)
    return s.text


def context_version(parts: list[Section]) -> str:
    """"ctx-" and the first twelve hex digits of a SHA-256 over the context's configuration:
    every section's name, where it is sent and its content, except the session so far and the
    question; and the layout, the name and place of every section in order.

    The same context gives the same version. One changed word in the standing orders, a
    changed memory, a changed tool schema, a section moved or dropped: another version. A new
    question, or a longer session: the same version (they are recorded beside it).
    """
    # TODO 1: the layout: [name, where] for every section, in order (the session and the
    #         question too: where they sit is part of the layout).
    # TODO 2: the content: [name, where, content(s)] for every section not in SESSION_PARTS.
    # TODO 3: hash a canonical JSON of both (json.dumps(..., sort_keys=True)) with SHA-256.
    # TODO 4: return "ctx-" and the first twelve hex digits.
    raise NotImplementedError("write context_version")
