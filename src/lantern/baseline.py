"""The baseline: a signed question set, a grader in code, and one score for one context.

Chapter 02 builds it. Every later chapter changes one thing in the context and calls
`score()` again on the same questions and the same seed.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Callable
from dataclasses import replace
from typing import Any

from lantern import case, context, tools
from lantern.context import HISTORY, QUESTION, Section
from lantern.llm import tool_result

QUESTIONS = "questions/questions.jsonl"
SIGNOFF = "questions/signoff.md"
NOT_IN_EVIDENCE = "not in evidence"
SEED = 7


def signed_hash() -> str:
    """The SHA-256 Okafor signed, read from the sign-off."""
    found = re.search(r"`([0-9a-f]{64})`", case.read(SIGNOFF))
    if not found:
        raise ValueError(f"no SHA-256 in case/{SIGNOFF}")
    return found.group(1)


def questions() -> list[dict[str, Any]]:
    """The signed question set. Refuses a file that is not the one that was signed."""
    text = case.read(QUESTIONS)
    got = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if got != signed_hash():
        raise ValueError(f"case/{QUESTIONS} is not the file that was signed: {got[:12]}...")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def normal(text: str) -> str:
    """Lower case, with the commas taken out of numbers: 1,183,369.26 reads as 1183369.26."""
    return re.sub(r"(?<=\d),(?=\d)", "", text).lower()


def says(text: str, value: str) -> bool:
    """Is `value` in `text` as a whole word or number, not as part of a longer one?"""
    return re.search(rf"(?<![\w.]){re.escape(normal(value))}(?!\w)", normal(text)) is not None


def first_word(text: str) -> str:
    words = re.findall(r"[a-z]+", text.lower())
    return words[0] if words else ""


def grade(answer: str, expect: dict[str, Any]) -> bool:
    """Does the answer meet what the signed record expects? Every condition given must hold."""
    if not answer.strip():
        return False
    if expect.get("or_not_in_evidence") and says(answer, NOT_IN_EVIDENCE):
        return True
    if "starts" in expect and first_word(answer) != expect["starts"]:
        return False
    if not all(says(answer, v) for v in expect.get("all", [])):
        return False
    if "any" in expect and not any(says(answer, v) for v in expect["any"]):
        return False
    return not any(normal(v) in normal(answer) for v in expect.get("none", []))


def reserve_lookup() -> list[dict[str, Any]]:
    """Two more turns for the session: the reserve's statement, looked up as the client's was."""
    rows = case.rows("statements/MTB-31-02290.csv")
    result = {"account_no": "MTB-31-02290", "holder": "Pellmar Nominees Ltd re Reserve 2",
              "bank": "Meridian Trust Bank", "as_of": "2026-07-06T06:00:00", "held": True,
              "pending": [], "balance": rows[-1]["balance"], "lines": rows}
    return [
        {"role": "assistant", "content": "", "tool_calls": [{"function": {
            "name": "statement", "arguments": {"account_no": "MTB-31-02290", "since": ""}}}]},
        {"role": "tool", "tool_name": "statement", "content": json.dumps(result)},
    ]


def with_evidence(parts: list[Section]) -> list[Section]:
    """The sections with the reserve's statement added to the session, for every question."""
    out = []
    for s in parts:
        if s.where == HISTORY:
            turns = [*s.payload, *reserve_lookup()]
            s = replace(s, text="".join(context._turn(m) for m in turns), payload=turns)
        out.append(s)
    return out


def asking(parts: list[Section], question: str) -> list[Section]:
    """The same sections with another question as the last turn."""
    return [replace(s, text=question + "\n") if s.where == QUESTION else s for s in parts]


def answer(messages: list[dict[str, Any]], schemas: list[dict[str, Any]], *,
           chat: Callable[..., Any], seed: int, max_tokens: int,
           max_tool_turns: int = 3) -> dict[str, Any]:
    """One question to its answer, running any tools the model calls (at most three rounds)."""
    messages, called, prompt_tokens = list(messages), [], 0
    for _ in range(max_tool_turns + 1):
        r = chat(messages, tools=schemas, seed=seed, max_tokens=max_tokens)
        prompt_tokens = max(prompt_tokens, r.prompt_tokens)
        if not r.tool_calls or len(called) >= max_tool_turns:
            break
        messages.append(r.message)
        for c in r.tool_calls:
            called.append(c.name)
            messages.append(tool_result(c.name, tools.run(c.name, c.arguments)))
    return {"answer": r.text, "called": called, "prompt_tokens": prompt_tokens}


def score(parts: list[Section], *, chat: Callable[..., Any], seed: int = SEED,
          max_tokens: int = 160, only: list[str] | None = None,
          grade: Callable[[str, dict[str, Any]], bool] = grade) -> list[dict[str, Any]]:
    """Ask every signed question with these sections as the context, and grade each answer.

    `only` asks a subset by id; `grade` swaps the grader (for a learner's own, with --mine).
    """
    parts = with_evidence(parts)
    out = []
    for q in questions():
        if only and q["id"] not in only:
            continue
        messages, schemas = context.request(asking(parts, q["question"]))
        got = answer(messages, schemas, chat=chat, seed=seed, max_tokens=max_tokens)
        out.append({"id": q["id"], "slice": q["slice"], "question": q["question"], **got,
                    "passed": grade(got["answer"], q["expect"])})
    if not out:
        raise ValueError("no questions were asked")
    return out


def wilson(passed: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """The 95% Wilson interval for `passed` of `n`, as fractions."""
    if n == 0:
        raise ValueError("an interval needs at least one question")
    p = passed / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def changed(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Which questions changed verdict between two runs of the same set."""
    was = {r["id"]: r["passed"] for r in before}
    now = {r["id"]: r["passed"] for r in after}
    if was.keys() != now.keys():
        raise ValueError("the two runs did not ask the same questions")
    return {"fixed": [i for i in was if now[i] and not was[i]],
            "broken": [i for i in was if was[i] and not now[i]]}


def by_slice(results: list[dict[str, Any]]) -> dict[str, tuple[int, int]]:
    """Passed and asked, per slice, in the order the slices first appear."""
    out: dict[str, tuple[int, int]] = {}
    for r in results:
        p, n = out.get(r["slice"], (0, 0))
        out[r["slice"]] = (p + r["passed"], n + 1)
    return out
