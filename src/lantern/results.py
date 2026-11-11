"""What happens to a tool result after the turn it was asked for.

Chapter 09 builds these. Each is a `before_request` hook for `lantern.agent.run`: it is given
the conversation and returns the conversation to send. The newest tool result is never
touched; the agent has not read it yet.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Messages = list[dict[str, Any]]
CLEARED = "[Cleared to save room."
SUMMARY = "[Summary written by LANTERN"
SMALL = 400  # characters; a result this short is left as it is


def stub(call: str) -> str:
    return (f"{CLEARED} This was the result of {call}. You have already reported from it. Call "
            "it again only if you need a line of it.]")


def _old_results(messages: Messages) -> list[tuple[int, str]]:
    """(index, the call that produced it) for every tool result but the newest."""
    newest = max((i for i, m in enumerate(messages) if m["role"] == "tool"), default=-1)
    out, call = [], "a tool"
    for i, m in enumerate(messages):
        if m["role"] == "assistant" and m.get("tool_calls"):
            f = m["tool_calls"][0]["function"]
            call = f"{f['name']}({', '.join(str(v) for v in f.get('arguments', {}).values())})"
        if m["role"] == "tool" and i != newest:
            out.append((i, call))
    return out


def untouched(content: str) -> bool:
    return not content.startswith((CLEARED, SUMMARY)) and len(content) > SMALL


def clear_old(messages: Messages) -> Messages:
    """Every old tool result replaced by a line saying what it was and that it was cleared."""
    out = list(messages)
    for i, call in _old_results(messages):
        if untouched(out[i]["content"]):
            out[i] = {**out[i], "content": stub(call)}
    return out


def summarise_old(write: Callable[[str, str], str]) -> Callable[[Messages], Messages]:
    """Every old tool result replaced by a summary. `write(call, content)` writes it; the
    summary is marked as written by the model, because it was."""
    def hook(messages: Messages) -> Messages:
        out = list(messages)
        for i, call in _old_results(messages):
            if untouched(out[i]["content"]):
                text = write(call, out[i]["content"])
                out[i] = {**out[i], "content": f"{SUMMARY} from the result of {call}.]\n{text}"}
        return out
    return hook


def old_share(messages: Messages, count: Callable[[str], int]) -> tuple[int, int]:
    """Tokens of old tool results, and tokens of everything, in a conversation."""
    old = {i for i, _ in _old_results(messages)}
    sizes = [count(m.get("content") or "") for m in messages]
    return sum(sizes[i] for i in old), sum(sizes)
