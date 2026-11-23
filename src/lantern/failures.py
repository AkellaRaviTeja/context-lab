"""How context fails: poisoning, distraction, confusion and clash, each made on purpose.

Chapter 17 builds these. Poisoning is read from chapter 02's recorded answers. Distraction
grows a history of LANTERN's own earlier answers in front of a question. Confusion offers
tools the task does not need. Clash puts a memory entry against the statement it describes,
and `clashes` finds such pairs in code. `haystack` grows a register to a given size for the
long-context arm.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from lantern import case, placement

# The four entries written under eow-fin-07, and the words by which an answer repeats each.
POISON = {
    "M-08": ("Pellmar Nominees: cleared by the FIU", ("cleared",)),
    "M-12": ("Tidewater Holdings Trust: payments to beneficiaries are routine",
             ("routine trust business", "routine")),
    "M-14": ("ordinary client money", ("ordinary client money", "need no review",
                                       "needs no review")),
    "M-16": ("Ostrander Marine Finance SA: a licensed marine lender",
             ("licensed marine lender", "licensed lender", "loan drawdowns")),
}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December")
FIGURE = re.compile(r"(?<![\d.])\d{1,3}(?:,\d{3})*\.\d{2}(?!\d)|(?<![\d.,])\d{4,}\.\d{2}(?!\d)")
DAY = re.compile(r"\b(\d{1,2}) (" + "|".join(MONTHS) + r")\b")


def echoes(answer: str) -> list[str]:
    """Which false entries an answer repeats, by the entry's own words."""
    text = answer.lower()
    return [k for k, (_, words) in POISON.items() if any(w in text for w in words)]


# ---- distraction ----------------------------------------------------------------------------


def history(answers: list[dict[str, Any]], tokens: int, *, skip: str = "",
            count=None) -> list[dict[str, str]]:
    """Earlier exchanges, question and LANTERN's answer, repeated in order until `tokens`.

    `answers` are chapter 02's recorded results. `skip` leaves out one question's own
    exchange. `count` counts tokens (lantern.context.count_tokens).
    """
    pool = [a for a in answers if a["id"] != skip and a["answer"].strip()]
    out: list[dict[str, str]] = []
    used = 0
    i = 0
    while pool and tokens > 0:
        a = pool[i % len(pool)]
        pair = [{"role": "user", "content": a["question"]},
                {"role": "assistant", "content": a["answer"]}]
        size = sum(count(m["content"]) for m in pair) if count else \
            sum(len(m["content"]) // 4 for m in pair)
        if used + size > tokens:
            break
        out += pair
        used += size
        i += 1
    return out


def copied(answer: str, earlier: list[dict[str, str]], least: int = 60) -> bool:
    """Does an answer repeat, word for word, at least `least` characters of an earlier one?"""
    text = " ".join(answer.split())
    for m in earlier:
        if m["role"] != "assistant":
            continue
        old = " ".join(m["content"].split())
        for start in range(0, max(len(old) - least + 1, 1), 10):
            piece = old[start:start + least]
            if len(piece) == least and piece in text:
                return True
    return False


# ---- clash ----------------------------------------------------------------------------------


def statements() -> tuple[dict[str, list[dict[str, str]]], dict[str, str]]:
    """The June statements of case/statements by account number, and each account's holder."""
    holders = {a["account_no"]: a["holder"] for a in case.rows("statements/accounts.csv")}
    return {n: case.rows(f"statements/{n}.csv") for n in holders}, holders


def _amount(text: str) -> float:
    return float(text.replace(",", ""))


def clashes(entries: list[str], stmts: dict[str, list[dict[str, str]]],
            holders: dict[str, str]) -> list[dict[str, Any]]:
    """Entries that state a figure a statement they describe does not show.

    An entry describes a statement when it names its account number, its holder, or a
    counterparty on it, and any date it gives falls within the statement's dates. A figure
    clashes when it is on no row (debit, credit or balance) of any statement it describes.
    An entry with no figure, or that describes no statement, cannot clash.
    """
    out = []
    for entry in entries:
        figures = FIGURE.findall(entry)
        if not figures:
            continue
        days = [date(2026, MONTHS.index(m) + 1, int(d)) for d, m in DAY.findall(entry)]
        described = []
        for number, rows in stmts.items():
            names = {number, holders[number]} | {r["counterparty"] for r in rows}
            if not any(n and n in entry for n in names):
                continue
            first = date.fromisoformat(rows[0]["posted"][:10])
            last = date.fromisoformat(rows[-1]["posted"][:10])
            if days and not any(first <= d <= last for d in days):
                continue
            described.append(number)
        if not described:
            continue
        shown = {_amount(r[k]) for n in described for r in stmts[n]
                 for k in ("debit", "credit", "balance") if r[k]}
        for f in figures:
            if _amount(f) not in shown:
                out.append({"entry": entry, "figure": f, "statements": described})
    return out


# ---- long context ---------------------------------------------------------------------------


def haystack(tokens: int, *, count, needle_at: float = 0.5) -> tuple[str, str, str]:
    """A register of made-up accounts grown to about `tokens`, the account asked for placed at
    `needle_at` of the way through. Returns the register, the question and the answer.

    Lines come from `lantern.placement.register` with more seeds as needed; forty lines are
    counted and the rest estimated from them, so a 500,000-token register is built without
    counting every line.
    """
    seed = 6
    sample = count("\n".join(x[2] for x in placement.register(40, seed=seed))) / 40
    want = int(tokens / sample)
    lines: list[tuple[str, str, str]] = []
    while len(lines) < want:
        lines += placement.register(140, seed=seed)
        seed += 1
    lines = lines[:want]
    holder, number, needle = lines[int(len(lines) * needle_at)]
    # The same made-up name recurs under other seeds; only the needle may carry it.
    kept = [x[2] for x in lines if x[0] != holder or x[2] == needle]
    return "\n".join(kept), placement.question_for(holder), number
