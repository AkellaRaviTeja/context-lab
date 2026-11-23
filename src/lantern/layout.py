"""Layout for the cache: what changes least goes first, what changes most goes last.

Chapter 16 builds it. A model server keeps its work on the beginning of the last prompt it
read and starts again from the first token that differs. `layout` orders the sections of a
context by how often each changes and marks where each group ends; `request` turns that order
into an Ollama request; `hosted_request` turns it into an Anthropic request with a cache
breakpoint at the end of each stable group (at most four, the API's limit); `session_cost`
prices a session from token counts, as a calculation and not a bill.

On Ollama the chat template decides where tool schemas go: straight after the system message.
So the system message holds only what comes before the tools in the layout, and every later
section travels as a user turn of its own.
"""

from __future__ import annotations

import json
from typing import Any

from lantern import hosted
from lantern.context import HISTORY, QUESTION, SYSTEM, TOOLS, Section

CHANGES = ("rarely", "weekly", "nightly", "per turn", "per question")
MAX_BREAKPOINTS = 4
HOW_OFTEN = {"standing orders": "rarely", "tool schemas": "rarely", "standing notes": "weekly",
             "case memory": "nightly", "session so far": "per turn",
             "the question": "per question"}


def how_often(name: str) -> str:
    """How often one of LANTERN's sections changes. The summaries are written each Friday."""
    return "weekly" if name.startswith("summary ") else HOW_OFTEN[name]


def layout(parts: list[Section], changes: dict[str, str]) -> tuple[list[Section], list[int]]:
    """The sections ordered from the one that changes least to the one that changes most, and
    the index of the last section of every group but the last: where a cache breakpoint goes.

    Sections that change equally often keep the order they were given in.
    """
    for p in parts:
        if changes.get(p.name) not in CHANGES:
            raise ValueError(f"{p.name!r}: how often it changes must be one of {CHANGES}")
    ordered = sorted(parts, key=lambda p: CHANGES.index(changes[p.name]))
    ends = [i for i in range(len(ordered) - 1)
            if changes[ordered[i].name] != changes[ordered[i + 1].name]]
    return ordered, ends[:MAX_BREAKPOINTS]


def request(ordered: list[Section]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """An Ollama request in this order: system text before the tools, everything else after.

    For today's order, where every system section comes before the tools, this is the request
    `lantern.context.request` makes.
    """
    tools_at = next((i for i, s in enumerate(ordered) if s.where == TOOLS), len(ordered))
    system = "\n".join(s.text for s in ordered[:tools_at] if s.where == SYSTEM)
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}] if system else []
    for s in ordered[tools_at:]:
        if s.where == SYSTEM:
            messages.append({"role": "user", "content": s.text.strip()})
        elif s.where == HISTORY:
            messages += s.payload
        elif s.where == QUESTION:
            messages.append({"role": "user", "content": s.text.strip()})
    schemas = [t for s in ordered if s.where == TOOLS for t in s.payload]
    return messages, schemas


def hosted_request(ordered: list[Section], breakpoints: list[int], *, model: str,
                   max_tokens: int, ttl: str = "5m") -> dict[str, Any]:
    """The Anthropic request for this layout, with a breakpoint at the end of each group.

    `lantern.hosted.build_request` builds it with caching off; the breakpoints are then put on
    the blocks where the groups end. Anthropic reads tools, then system, then messages, so a
    group that ends with the system message or the tools gets its breakpoint on the last
    system block, which covers both.
    """
    if len(breakpoints) > MAX_BREAKPOINTS:
        raise ValueError(f"at most {MAX_BREAKPOINTS} cache breakpoints, not {len(breakpoints)}")
    messages, schemas = request(ordered)
    kwargs, _, _ = hosted.build_request(messages, model=model, max_tokens=max_tokens,
                                        tools=schemas, cache="none")
    marker = {"type": "ephemeral"} if ttl == "5m" else {"type": "ephemeral", "ttl": ttl}
    tools_at = next((i for i, s in enumerate(ordered) if s.where == TOOLS), len(ordered))
    for b in breakpoints:
        if b < tools_at or ordered[b].where == TOOLS:
            if kwargs.get("system"):
                kwargs["system"][-1] = {**kwargs["system"][-1], "cache_control": marker}
            elif kwargs.get("tools"):
                kwargs["tools"][-1] = {**kwargs["tools"][-1], "cache_control": marker}
            continue
        upto, _ = request(ordered[:b + 1])
        n = len(hosted.to_anthropic(upto)[1]) - 1
        msg = kwargs["messages"][n]
        blocks = msg["content"] if isinstance(msg["content"], list) else \
            [{"type": "text", "text": msg["content"]}]
        blocks = [*blocks[:-1], {**blocks[-1], "cache_control": marker}]
        kwargs["messages"][n] = {**msg, "content": blocks}
    return kwargs


def breakpoints_in(kwargs: dict[str, Any]) -> int:
    """How many cache breakpoints a request carries."""
    return json.dumps(kwargs).count('"cache_control"')


def session_cost(*, stable: int, tail: int, output: int, questions: int, writes: int,
                 prices: dict[str, float], ttl: str = "5m", cached: bool = True) -> float:
    """US dollars for a session, priced from token counts: a calculation, not a bill.

    Every question sends `stable` tokens of prefix, `tail` tokens after it and gets `output`
    back. With caching, `writes` of the questions write the prefix to the cache and the rest
    read it. Without, every token is input.
    """
    if not cached:
        return questions * ((stable + tail) * prices["input"] + output * prices["output"]) / 1e6
    write = prices["cache_write_1h"] if ttl == "1h" else prices["cache_write_5m"]
    reads = questions - writes
    return (writes * stable * write + reads * stable * prices["cache_read"]
            + questions * (tail * prices["input"] + output * prices["output"])) / 1e6
