"""A small agent loop that keeps a record of what every request carried.

Chapters 08 to 11 and 15 use it. It does one thing the loops of Case File 02 did not: before
each request it can check the conversation against a budget and stop, saying so, where a
server would have cut the oldest turns without a word.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from lantern import context
from lantern.llm import tool_result

Handler = Callable[..., Any]


@dataclass
class Turn:
    """One request: what it carried, by kind, and what came back."""

    n: int
    prompt_tokens: int
    by_role: dict[str, int]
    calls: list[tuple[str, dict[str, Any]]]
    text: str


@dataclass
class Run:
    answer: str = ""
    turns: list[Turn] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    stopped: str = ""  # why the loop ended: "answered", "turn limit", "over budget", ...
    sent_back: int = 0  # answers the check in code refused

    @property
    def calls(self) -> list[tuple[str, dict[str, Any]]]:
        return [c for t in self.turns for c in t.calls]

    @property
    def total_prompt_tokens(self) -> int:
        return sum(t.prompt_tokens for t in self.turns)

    @property
    def largest_request(self) -> int:
        return max((t.prompt_tokens for t in self.turns), default=0)


def weigh(messages: list[dict[str, Any]], schemas: list[dict[str, Any]] | None = None
          ) -> dict[str, int]:
    """Tokens in a conversation by role, counted message by message, plus the tool schemas."""
    out: dict[str, int] = {}
    for m in messages:
        text = m.get("content") or json.dumps(m.get("tool_calls", []))
        out[m["role"]] = out.get(m["role"], 0) + context.count_tokens(text)
    if schemas:
        out["tool schemas"] = context.count_tokens("\n".join(json.dumps(t) for t in schemas))
    return out


def run(messages: list[dict[str, Any]], *, chat: Callable[..., Any],
        schemas: list[dict[str, Any]], handlers: dict[str, Handler], max_turns: int = 12,
        max_tokens: int = 500, seed: int = 7, limit: int | None = None,
        before_request: Callable[[list[dict[str, Any]]], list[dict[str, Any]]] | None = None,
        until: Callable[[str], str | None] | None = None,
        ) -> Run:
    """Run the loop until the model answers without a tool call, or a limit stops it.

    `limit` is the most tokens a request may carry, counted before it is sent; over it the
    loop stops and says so. `before_request` may rewrite the conversation before each request
    (trimming, clearing, compacting): it returns the messages to send and to keep.
    `until` is a check in code on every answer: it returns None when the task is done, or
    what is still missing, which is sent back to the model as the next turn.
    """
    out = Run(messages=list(messages))
    seen: dict[str, int] = {}
    for n in range(1, max_turns + 1):
        if before_request:
            out.messages = before_request(out.messages)
        weight = weigh(out.messages, schemas)
        if limit is not None and sum(weight.values()) > limit:
            out.stopped = (f"over budget before turn {n}: {sum(weight.values()):,} tokens "
                           f"against a limit of {limit:,}")
            return out
        r = chat(out.messages, tools=schemas, seed=seed, max_tokens=max_tokens)
        calls = [(c.name, c.arguments) for c in r.tool_calls]
        out.turns.append(Turn(n, r.prompt_tokens, weight, calls, r.text))
        if not calls:
            out.answer = r.text
            missing = until(r.text) if until else None
            if missing is None:
                out.stopped = "answered"
                return out
            out.sent_back += 1
            out.messages += [r.message, {"role": "user", "content": missing}]
            continue
        out.messages.append(r.message)
        for name, arguments in calls:
            key = name + json.dumps(arguments, sort_keys=True)
            seen[key] = seen.get(key, 0) + 1
            if name not in handlers:
                result: Any = {"failed": True, "error": f"There is no tool named {name!r}."}
            elif seen[key] > 2:
                result = {"failed": True, "error": "You have made this exact call before. "
                          "Use what it returned, or call something else."}
            else:
                try:
                    result = handlers[name](**arguments)
                except TypeError as e:
                    result = {"failed": True, "error": f"Bad arguments for {name}: {e}"}
            out.messages.append(tool_result(name, result))
    out.stopped = "turn limit"
    return out
