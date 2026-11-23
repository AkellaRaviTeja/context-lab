"""Chapter 23 solution: the context version, a hash over what LANTERN is given."""

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
    question; and the layout, the name and place of every section in order."""
    body = {"layout": [[s.name, s.where] for s in parts],
            "sections": [[s.name, s.where, content(s)] for s in parts
                         if s.where not in SESSION_PARTS]}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()
    return "ctx-" + digest[:12]
