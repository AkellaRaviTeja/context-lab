"""Working notes for one task, kept outside the window.

Chapter 11 builds it. The agent writes a note with a tool; the note is kept in a file; and the
notebook can be read back into a new conversation after a compaction or a restart. Two rules
make the notes checkable: a flow must name the statement it came from, and the note is
compared with what that statement's tool result said before it is kept.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lantern import trail

RULE = ("After every money_out call, write one note_flow for each payee that is not a bank, "
        "before you do anything else. Your notes are kept for you outside this conversation. ")


@dataclass
class Notebook:
    """Flows found and questions open, for one task. `path` is where it is kept."""

    path: Path
    flows: list[dict[str, Any]] = field(default_factory=list)
    questions: list[dict[str, Any]] = field(default_factory=list)
    refused: list[str] = field(default_factory=list)

    @classmethod
    def open(cls, path: Path) -> Notebook:
        """The notebook at `path`, or an empty one if nothing is there yet."""
        if path.exists():
            kept = json.loads(path.read_text(encoding="utf-8"))
            return cls(path, kept["flows"], kept["questions"], kept.get("refused", []))
        return cls(path)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(
            {"flows": self.flows, "questions": self.questions, "refused": self.refused},
            indent=1), encoding="utf-8")

    # ---- what the agent may write -------------------------------------------------------------

    def note_flow(self, payer: str = "", payee: str = "", payments: Any = "", total: Any = "",
                  source: str = "", **_: Any) -> dict[str, Any]:
        """Keep one flow, if it names its source and agrees with it."""
        problem = self.problem_with(payer, payee, payments, total, source)
        if problem:
            self.refused.append(problem)
            self.save()
            return {"kept": False, "refused": problem}
        note = {"payer": payer, "payee": payee, "payments": int(number(payments)),
                "total": f"{number(total):.2f}", "source": source}
        self.flows = [f for f in self.flows if (f["payer"], f["payee"]) != (payer, payee)]
        self.flows.append(note)
        self.save()
        return {"kept": True, "flows_noted": len(self.flows)}

    def problem_with(self, payer: str, payee: str, payments: Any, total: Any, source: str
                     ) -> str | None:
        """Why a flow cannot be kept, or None. The source's own digest is the test."""
        return problem_with(payer, payee, payments, total, source, digest=trail.digest,
                            holder_of=holder)

    def note_question(self, question: str = "", **_: Any) -> dict[str, Any]:
        self.questions.append({"id": len(self.questions) + 1, "question": question,
                               "answer": None})
        self.save()
        return {"kept": True, "id": len(self.questions)}

    def close_question(self, id: Any = 0, answer: str = "", **_: Any) -> dict[str, Any]:
        for q in self.questions:
            if q["id"] == int(id):
                q["answer"] = answer
                self.save()
                return {"closed": True}
        return {"closed": False, "error": f"no question {id}"}

    # ---- what is read back --------------------------------------------------------------------

    def sources(self) -> list[str]:
        """The statements the notes were read from, in the order first noted."""
        return list(dict.fromkeys(f["source"] for f in self.flows))

    def text(self) -> str:
        """The notebook as it is put back in front of the agent."""
        if not self.flows and not self.questions:
            return "Your notes for this task: none yet."
        lines = ["Your notes for this task, each checked against its source when written:"]
        lines += [f"- {f['payer']} -> {f['payee']} | {f['payments']} payments | total "
                  f"{f['total']} | from {f['source']}" for f in self.flows]
        still = [q for q in self.questions if q["answer"] is None]
        lines += [f"- open question {q['id']}: {q['question']}" for q in still]
        return "\n".join(lines)

    def tools(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        schemas = [
            trail.schema("note_flow", "Write down one flow you have read from a statement.",
                         payer="The account holder that paid.", payee="Who was paid.",
                         payments="The number of payments.", total="The total paid.",
                         source="The file the flow was read from."),
            trail.schema("note_question", "Write down a question you cannot answer yet.",
                         question="The question."),
            trail.schema("close_question", "Close a question you wrote down.",
                         id="The question's number.", answer="What you found."),
        ]
        return schemas, {"note_flow": self.note_flow, "note_question": self.note_question,
                         "close_question": self.close_question}


def holder(file: str) -> str | None:
    """Whose statement `file` is, or None when no statement by that name is on file."""
    return next((a["holder"] for a in trail.accounts() if a["file"] == file), None)


def number(value: Any) -> float | None:
    """A figure as a number, or None. A model may write 9, "9", 9.0 or "2,262,000.00"; None, a
    list or "n/a" is no figure."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except ValueError:
            return None
    return None


def problem_with(payer: str, payee: str, payments: Any, total: Any, source: str, *,
                 digest: Callable[[str], dict[str, Any]],
                 holder_of: Callable[[str], str | None]) -> str | None:
    """Why a flow cannot be kept, or None when it can. The source's own digest is the test.

    `holder_of(file)` is the account holder of a statement, or None when there is no such
    statement; `digest(file)` is what the statement tool returned for it. The checks run in
    order and the first that fails is the reason.
    """
    if not source:
        return "a note needs its source: the file the flow was read from"
    owner = holder_of(source)
    if owner is None:
        return f"no statement named {source!r} is on file"
    if owner != payer:
        return f"{source} is the statement of {owner}, not of {payer}"
    paid = {p["payee"]: p for p in digest(source)["paid_out_to"]}
    if payee not in paid:
        return f"{source} shows no payment to {payee}"
    n, t = number(payments), number(total)
    if n is None or t is None or n != int(n):
        return "payments must be a whole number and total a figure"
    if abs(t - float(paid[payee]["total"])) > 0.005:
        return f"{source} gives {paid[payee]['total']} to {payee}, the note says {total}"
    if int(n) != paid[payee]["payments"]:
        return (f"{source} shows {paid[payee]['payments']} payments to {payee}, the note says "
                f"{payments}")
    return None
