"""Chapter 09 reference solution: clear a used tool result, and say that it was cleared."""

from __future__ import annotations

from typing import Any

Messages = list[dict[str, Any]]
CLEARED = "[Cleared to save room."
SMALL = 400  # characters; a result this short is left as it is


def stub(call: str) -> str:
    return (f"{CLEARED} This was the result of {call}. You have already reported from it. Call "
            "it again only if you need a line of it.]")


def clear_old(messages: Messages) -> Messages:
    """Every old tool result replaced by a line saying what it was and that it was cleared."""
    newest = max((i for i, m in enumerate(messages) if m["role"] == "tool"), default=-1)
    out, call = [], "a tool"
    for i, m in enumerate(messages):
        if m["role"] == "assistant" and m.get("tool_calls"):
            f = m["tool_calls"][0]["function"]
            call = f"{f['name']}({', '.join(str(v) for v in f.get('arguments', {}).values())})"
        if (m["role"] == "tool" and i != newest and len(m["content"]) > SMALL
                and not m["content"].startswith(CLEARED)):
            m = {**m, "content": stub(call)}
        out.append(m)
    return out
