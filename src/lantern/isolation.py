"""Isolating context: a reader that works in a window of its own and returns a few lines.

Chapter 15 builds it. The nine statements of the trail are cut into pages, as a bank prints
them. The main agent may read the pages itself, or send a reader (a sub-agent) to one
statement with `delegate`. The reader starts with an empty context, reads the pages, and
returns at most five lines, each naming the pages it came from, and the pages it did not read.
`check_report` refuses a report without those. `hidden` compares a report with the statement
in code: what the main agent cannot see, because it never held the pages.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from lantern import agent, baseline, case, trail

PAGE_LINES = 18  # statement lines a page, as the bank prints them
MAX_LINES = 5  # the most a reader may report
NONE_WORDS = {"none", "nothing", "no pages", "-", "n/a"}
LINE = re.compile(r"^\s*[-*]*\s*LINE:\s*(.+?)\s*->\s*(.+?)\s*\|\s*(\d+)\s*payments?\s*\|\s*"
                  r"total\s*([\d,]+(?:\.\d+)?)\s*(?:\|\s*(.*))?$", re.I | re.M)
NOT_READ = re.compile(r"^\s*[-*]*\s*NOT READ:\s*(.*)$", re.I | re.M)
PAGE_ID = re.compile(r"[a-z][a-z-]*\.p\d+", re.I)
CheckReport = Callable[[str, list[str]], list[str]]


@dataclass(frozen=True)
class Page:
    id: str  # corvane-trading.p1
    file: str  # corvane-trading.csv
    n: int
    of: int
    first: str  # the first date on the page
    last: str
    text: str


def pages(lines: int = PAGE_LINES) -> list[Page]:
    """Every statement of the trail, cut into pages of `lines` rows, in accounts.csv order."""
    out = []
    for a in trail.accounts():
        rows = case.read(f"bank/{a['file']}").splitlines()
        header, body = rows[0], rows[1:]
        chunks = [body[i:i + lines] for i in range(0, len(body), lines)]
        stem = a["file"].removesuffix(".csv")
        for n, chunk in enumerate(chunks, 1):
            text = (f"Page {n} of {len(chunks)}: {a['holder']}, account {a['account_no']}, "
                    f"{a['bank']}.\n{header}\n" + "\n".join(chunk))
            out.append(Page(f"{stem}.p{n}", a["file"], n, len(chunks), chunk[0][:10],
                            chunk[-1][:10], text))
    return out


def page_listing(all_pages: list[Page]) -> str:
    """The pages as the agent that reads them itself sees them: id, holder, dates."""
    holders = {a["file"]: a["holder"] for a in trail.accounts()}
    return "Statement pages on file:\n" + "\n".join(
        f"- {p.id}: {holders[p.file]}, page {p.n} of {p.of}, {p.first} to {p.last}"
        for p in all_pages)


def statement_listing(all_pages: list[Page]) -> str:
    """The statements as the main agent that delegates sees them, with their page counts."""
    count: dict[str, int] = {}
    for p in all_pages:
        count[p.file] = count.get(p.file, 0) + 1
    return "Statements on file:\n" + "\n".join(
        f"- {a['file']}: {a['holder']}, {a['account_no']}, {a['bank']}, {count[a['file']]} "
        "pages." for a in trail.accounts())


# ---- the report ------------------------------------------------------------------------------


def parse(report: str) -> tuple[list[dict[str, Any]], list[str] | None]:
    """The LINE lines of a report, and the pages it says it did not read (None: no such line)."""
    lines = [{"payer": a.strip(" *"), "payee": b.strip(" *"), "payments": int(n),
              "total": float(t.replace(",", "")),
              "sources": PAGE_ID.findall(rest or "")}
             for a, b, n, t, rest in LINE.findall(report)]
    m = NOT_READ.search(report)
    not_read = None if m is None else PAGE_ID.findall(m.group(1))
    return lines, not_read


def check_report(report: str, page_ids: list[str]) -> list[str]:
    """What is wrong with a reader's report, in words; an empty list when it may be relied on.

    The report must have one to MAX_LINES LINE lines, each naming at least one source page
    that is one of `page_ids`, and a NOT READ line naming pages from `page_ids` or "none".
    """
    lines, not_read = parse(report)
    allowed = {p.lower() for p in page_ids}
    problems = []
    if not lines:
        problems.append("it has no LINE lines in the form asked")
    if len(lines) > MAX_LINES:
        problems.append(f"it has {len(lines)} LINE lines; the most allowed is {MAX_LINES}")
    for i, line in enumerate(lines, 1):
        if not line["sources"]:
            problems.append(f"LINE {i} names no source page")
        for s in line["sources"]:
            if s.lower() not in allowed:
                problems.append(f"LINE {i} names {s}, which is not one of your pages")
    if not_read is None:
        problems.append("it has no NOT READ line")
    else:
        text = NOT_READ.search(report).group(1).strip().strip(".").lower()
        if not not_read and text not in NONE_WORDS:
            problems.append("the NOT READ line names no pages and does not say none")
        for s in not_read:
            if s.lower() not in allowed:
                problems.append(f"NOT READ names {s}, which is not one of your pages")
    return problems


# ---- the reader -----------------------------------------------------------------------------

READER = ("You are a reader working for LANTERN, the analysis workstation of the Economic "
          "Offences Wing, Kestrel Bay Police. You have a window of your own and nothing else: "
          "no earlier conversation and no other files. Read the pages you are given with "
          "read_page, one call a page, then report in exactly this form and nothing else:\n"
          "LINE: <payer> -> <payee> | <number of payments> payments | total <amount> | "
          "source: <page ids>\n"
          f"At most {MAX_LINES} LINE lines. Each names the pages it rests on. Then one line:\n"
          "NOT READ: <the page ids you did not read, or none>\n")
FULL = ("Your window is nearly full. Read nothing more. Report now from the pages you have "
        "read, and list every page you have not read on the NOT READ line.")
TELL = "Write the task in full: the reader sees nothing of your conversation."


def page_schema() -> dict[str, Any]:
    return trail.schema("read_page", "One page of a bank statement, every line as the bank "
                        "printed it.", page="A page id from the list, such as corvane-trading.p1.")


def read(file: str, task: str, *, chat: Callable[..., Any], limit: int, reserve: int = 600,
         check: CheckReport = check_report, max_turns: int = 10, seed: int = 7
         ) -> dict[str, Any]:
    """Send a reader to one statement in a fresh context. Returns its report and its record."""
    mine = [p for p in pages() if p.file == file]
    ids = [p.id for p in mine]
    text = {p.id: p.text for p in mine}
    opened: list[str] = []
    full = {"said": False}

    def read_page(page: str = "", **_: Any) -> Any:
        if full["said"]:
            return {"failed": True, "error": "No room is left in your window. Report now."}
        if page not in text:
            return {"failed": True, "error": f"No page named {page!r}.", "pages": ids}
        opened.append(page)
        return text[page]

    def before(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not full["said"] and sum(agent.weigh(messages, [page_schema()]).values()) > \
                0.8 * limit:
            full["said"] = True
            return [*messages, {"role": "user", "content": FULL}]
        return messages

    def until(report: str) -> str | None:
        problems = check(report, ids)
        if not problems:
            return None
        return ("Your report was refused: " + "; ".join(problems) + ". Give the whole report "
                "again in the form asked.")

    listing = "Your pages:\n" + "\n".join(f"- {p.id}: {p.first} to {p.last}" for p in mine)
    run = agent.run([{"role": "system", "content": READER + listing},
                     {"role": "user", "content": task}], chat=chat, schemas=[page_schema()],
                    handlers={"read_page": read_page}, max_turns=max_turns, max_tokens=reserve,
                    limit=limit, seed=seed, before_request=before, until=until)
    accepted = run.stopped == "answered"
    return {"file": file, "task": task, "pages": ids, "opened": list(dict.fromkeys(opened)),
            "report": run.answer, "accepted": accepted, "refused": run.sent_back,
            "stopped": run.stopped.split(":")[0], "tokens": run.total_prompt_tokens,
            "largest": run.largest_request, "requests": len(run.turns),
            "problems": [] if accepted else check(run.answer, ids)}


def hidden(record: dict[str, Any]) -> dict[str, Any]:
    """What a report got wrong or left out, checked in code against the statement itself.

    The main agent sees none of this: it has the report and never held the pages.
    """
    lines, not_read = parse(record["report"])
    truth = {f.payee.lower(): f for f in trail.flows_out(record["file"])}
    wrong_totals, wrong_counts, invented = [], [], []
    for line in lines:
        f = truth.get(line["payee"].lower())
        if f is None:
            invented.append(line["payee"])
            continue
        if abs(f.total - line["total"]) >= 0.005:
            wrong_totals.append(f"{f.payee}: reported {line['total']:,.2f}, statement "
                                f"{f.total:,.2f}")
        if f.payments != line["payments"]:
            wrong_counts.append(f"{f.payee}: reported {line['payments']}, statement "
                                f"{f.payments}")
    named = {line["payee"].lower() for line in lines}
    left_out = [f.payee for k, f in truth.items() if k not in named]
    unopened = [p for p in record["pages"] if p not in record["opened"]]
    claimed = {s.lower() for line in lines for s in line["sources"]}
    cited_unopened = sorted(c for c in claimed if c not in {o.lower() for o in record["opened"]})
    not_said = [p for p in unopened if p.lower() not in {x.lower() for x in (not_read or [])}]
    return {"wrong_totals": wrong_totals, "wrong_counts": wrong_counts, "invented": invented,
            "left_out": left_out, "unopened": unopened, "cited_unopened": cited_unopened,
            "unread_not_said": not_said}


# ---- questions the report does not answer ---------------------------------------------------


def follow_ups() -> list[dict[str, Any]]:
    """Three questions whose answers are on the pages and in no five-line report.

    Each answer is read from the statements in code.
    """
    def first_debit(file: str, payee: str) -> dict[str, str]:
        return next(r for r in trail.statement(file) if r["debit"] and r["counterparty"] == payee)

    pel = first_debit("pellmar-nominees.csv", "Osprey Point Management Ltd")
    cal = first_debit("calder-reach.csv", "Pellmar Nominees Ltd")
    big = max((r for r in trail.statement("corvane-trading.csv")
               if r["debit"] and r["counterparty"] == "Lowmarsh Shipping Services Ltd"),
              key=lambda r: float(r["debit"]))
    return [
        {"id": "F-1", "q": "On what date did Pellmar Nominees Ltd first pay Osprey Point "
         "Management Ltd? Give the date as YYYY-MM-DD.", "answer": pel["date"]},
        {"id": "F-2", "q": "What reference did the first payment from Calder Reach Holdings Ltd "
         "to Pellmar Nominees Ltd carry?", "answer": cal["reference"]},
        {"id": "F-3", "q": "What was the largest single payment Corvane Trading Ltd made to "
         "Lowmarsh Shipping Services Ltd, and on what date?",
         "answer": [big["debit"], big["debit"].removesuffix(".00")], "also": big["date"]},
    ]


def answered(text: str, item: dict[str, Any]) -> bool:
    """Does an answer give the figure, reference or date the statement holds?"""
    forms = item["answer"] if isinstance(item["answer"], list) else [item["answer"]]
    return any(baseline.says(text, f) for f in forms) and \
        ("also" not in item or baseline.says(text, item["also"]))
