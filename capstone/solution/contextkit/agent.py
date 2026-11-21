"""An agent that answers from what its memory store may load, and writes through the policy."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from contextkit.builder import Section, build
from contextkit.memory import MemoryStore

REMEMBER = {"type": "function", "function": {
    "name": "remember",
    "description": "Propose one line for the case memory. It is kept only if it names its "
                   "source; otherwise it is held for an officer.",
    "parameters": {"type": "object", "properties": {
        "text": {"type": "string"}, "source": {"type": "string"}}, "required": ["text"]}}}


@dataclass
class Answer:
    text: str
    version: str
    loaded: list[str]
    dropped: list[str]
    prompt_tokens: int = 0
    proposed: list[dict[str, Any]] = field(default_factory=list)


def render(records) -> str:
    return "\n".join(f"- [{r.id}] {r.text} (source: {r.source or r.episode or 'none'}; "
                     f"{r.author}, {r.at[:10]})" for r in records)


def answer(question: str, *, store: MemoryStore, inquiry: str, chat: Callable[..., Any],
           rules: str, budget: int, count: Callable[[str], int], user: str | None = None,
           author: str = "lantern", at: str = "2026-08-07T09:00:00", k: int = 8,
           max_turns: int = 3) -> Answer:
    loaded = store.load(inquiry, user=user, query=question, k=k)
    sections = [Section("rules", rules, stable=True, required=True),
                Section("memory", "Case memory, each line with its source:\n"
                        + (render(loaded) or "(nothing loaded)"), priority=1),
                Section("question", question, required=True)]
    built = build(sections, budget=budget, count=count)
    text = {s.name: s.text for s in sections}
    shown = [r.id for r in loaded] if "memory" in built.order else []
    messages = [{"role": "system", "content": "\n\n".join(
                    text[name] for name in built.order if name != "question")},
                {"role": "user", "content": question}]
    proposed: list[dict[str, Any]] = []
    tokens = 0
    for n in range(max_turns):
        r = chat(messages, tools=[REMEMBER], seed=7)
        tokens += r.prompt_tokens
        if not r.tool_calls or n == max_turns - 1:
            return Answer(r.text, built.version, shown, built.dropped, tokens, proposed)
        messages.append(r.message)
        for call in r.tool_calls:
            if call.name != "remember":
                result: dict[str, Any] = {"failed": True, "error": f"no tool {call.name}"}
            else:
                rec = store.write(id=f"P-{len(store.all()) + 1:04d}",
                                  text=str(call.arguments.get("text", "")), kind="fact",
                                  inquiry=inquiry, author=author, at=at,
                                  source=call.arguments.get("source") or None, via="remember")
                result = {"id": rec.id, "status": rec.status, "problems": rec.problems}
                proposed.append(result)
            messages.append({"role": "tool", "tool_name": call.name,
                             "content": json.dumps(result)})
    raise AssertionError("unreachable")
