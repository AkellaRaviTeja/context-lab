"""What LANTERN is told before a question: the state of 13 July, assembled as it is today.

`sections()` returns every part in the order the workstation sends it. `request()` turns them
into the messages and tool schemas of one call. `count_tokens()` asks the model's own tokenizer.
Chapter 01 prints all of it; later chapters replace this assembly piece by piece.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from functools import lru_cache
from typing import Any

import httpx

from lantern import case
from lantern.config import load_config, model_name

SUMMARIES = ("month-2026-06.md", "week-2026-06-15.md", "week-2026-06-22.md",
             "week-2026-06-29.md", "week-2026-07-06.md")
# Where each section travels in the request: inside the system message, as tool schemas, as
# earlier turns of the conversation, or as the last user turn.
SYSTEM, TOOLS, HISTORY, QUESTION = "system", "tools", "history", "question"


@dataclass(frozen=True)
class Section:
    """One part of the input. `text` is what the model reads; `payload` is how it is sent."""

    name: str
    where: str
    text: str
    payload: Any = field(default=None, compare=False, repr=False)


def tools() -> list[dict[str, Any]]:
    """Every tool schema LANTERN has been given, without the date it was added."""
    return [{k: v for k, v in t.items() if k != "added"}
            for t in json.loads(case.read("state/tools.json"))]


def history() -> list[dict[str, Any]]:
    """Monday morning's session so far, as chat messages."""
    keep = ("role", "content", "tool_calls", "tool_name")
    return [{k: m[k] for k in keep if k in m} for m in case.jsonl("state/session-2026-07-13.jsonl")]


def question() -> str:
    return case.read("state/question.txt").strip()


def sections(ask: str | None = None) -> list[Section]:
    """Everything sent for one question on 13 July, in the order it is sent."""
    out = [
        Section("standing orders", SYSTEM, case.read("state/standing-orders.md")),
        Section("case memory", SYSTEM, case.read("state/case-memory.md")),
        Section("standing notes", SYSTEM, case.read("state/standing-notes.md")),
    ]
    out += [Section(f"summary {name[:-3]}", SYSTEM, case.read(f"state/summaries/{name}"))
            for name in SUMMARIES]
    schemas = tools()
    out.append(Section("tool schemas", TOOLS, "\n".join(json.dumps(t) for t in schemas) + "\n",
                       schemas))
    turns = history()
    out.append(Section("session so far", HISTORY, "".join(_turn(m) for m in turns), turns))
    out.append(Section("the question", QUESTION, (ask or question()) + "\n"))
    return out


def _turn(m: dict[str, Any]) -> str:
    """One earlier turn as text: the role, then what it said or called."""
    said = m.get("content") or json.dumps([c["function"] for c in m.get("tool_calls", [])])
    return f"{m['role']}: {said}\n"


def request(parts: list[Section]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The messages and tool schemas of one call, from its sections."""
    system = "\n".join(s.text for s in parts if s.where == SYSTEM)
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}] if system else []
    for s in parts:
        if s.where == HISTORY:
            messages += s.payload
    messages += [{"role": "user", "content": s.text.strip()} for s in parts if s.where == QUESTION]
    schemas = [t for s in parts if s.where == TOOLS for t in s.payload]
    return messages, schemas


def flat(parts: list[Section]) -> str:
    """The whole input as the one sequence of lines the model reads, in order."""
    return "".join(s.text if s.text.endswith("\n") else s.text + "\n" for s in parts)


def without(parts: list[Section], lines: list[str], only: str | None = None) -> list[Section]:
    """The same sections with every line containing one of `lines` removed.

    `only` limits the removal to one section. Sections sent as a payload (tools, history) are
    left alone: their text is a rendering, not what is sent. Raises if nothing was removed.
    """
    out, removed = [], 0
    for s in parts:
        if s.payload is None and s.where != QUESTION and only in (None, s.name):
            kept = [x for x in s.text.splitlines() if not any(line in x for line in lines)]
            removed += len(s.text.splitlines()) - len(kept)
            s = replace(s, text="\n".join(kept) + "\n")
        out.append(s)
    if not removed:
        raise ValueError(f"none of {lines!r} is in the sections")
    return out


@lru_cache(maxsize=4096)
def count_tokens(text: str, model: str | None = None) -> int:
    """How many tokens the model's own tokenizer makes of `text` (Ollama, raw, no template)."""
    if not text:
        return 0
    cfg = load_config()
    r = httpx.post(
        f"{cfg['ollama']['host']}/api/generate",
        json={"model": model_name(model), "prompt": text, "raw": True, "stream": False,
              "options": {"num_predict": 1, "num_ctx": 16384}},
        timeout=cfg["limits"]["request_timeout_s"],
    )
    r.raise_for_status()
    return int(r.json()["prompt_eval_count"])
