"""The trail of Case File 02 as a task: nine bank statements, and the flows between them.

Chapters 08 to 11 and 15 trace it. The right flows are computed here from the statements
themselves, never from anything a model said, and `grade()` reads a report against them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from lantern import case

BANKS = ("Sabran Commercial Bank", "Sabran Mercantile Bank", "Meridian Trust Bank",
         "Kestrel Bay Commercial Bank")
START = "Corvane Trading Ltd"
TASK = (f"Follow the money that {START} paid out, hop by hop, until it stops moving. For "
        "every hop report one line in exactly this form:\n"
        "FLOW: <payer> -> <payee> | <number of payments> payments | total <amount>\n"
        "Ignore bank charges and ignore anything paid back to Northwind Freight Ltd. The "
        "statements cover 1 January to 31 March 2026. Finish with the line DONE.")


@dataclass(frozen=True)
class Flow:
    payer: str
    payee: str
    payments: int
    total: float


def accounts() -> list[dict[str, str]]:
    return case.rows("bank/accounts.csv")


def statement(file: str) -> list[dict[str, str]]:
    return case.rows(f"bank/{file}")


def holder_of(file: str) -> str:
    return next(a["holder"] for a in accounts() if a["file"] == file)


def flows_out(file: str) -> list[Flow]:
    """Money out of one statement, by payee, bank charges left out."""
    by: dict[str, list[float]] = {}
    for r in statement(file):
        if r["debit"] and r["counterparty"] not in BANKS:
            by.setdefault(r["counterparty"], []).append(float(r["debit"]))
    return [Flow(holder_of(file), payee, len(v), round(sum(v), 2)) for payee, v in by.items()]


def expected() -> list[Flow]:
    """Every hop from START to where the money stops, as the statements show it."""
    files = {a["holder"]: a["file"] for a in accounts()}
    out, queue, seen = [], [START], set()
    while queue:
        holder = queue.pop(0)
        if holder in seen or holder not in files:
            continue
        seen.add(holder)
        for f in flows_out(files[holder]):
            if f.payee == "Northwind Freight Ltd":
                continue
            out.append(f)
            queue.append(f.payee)
    return out


LINE = re.compile(r"FLOW:\s*(.+?)\s*->\s*(.+?)\s*\|\s*(\d+)\s*payments?\s*\|\s*total\s*"
                  r"([\d,]+\.?\d*)", re.I)


def reported(report: str) -> list[Flow]:
    """The FLOW lines of a report, parsed. A line in any other form is not a flow."""
    return [Flow(a.strip(" *"), b.strip(" *"), int(n), float(t.replace(",", "")))
            for a, b, n, t in LINE.findall(report)]


def grade(report: str) -> dict[str, Any]:
    """A report against the statements: hops found, totals and counts right, hops invented."""
    want = {(f.payer.lower(), f.payee.lower()): f for f in expected()}
    got = {(f.payer.lower(), f.payee.lower()): f for f in reported(report)}
    found = [k for k in want if k in got]
    return {
        "expected": len(want),
        "found": len(found),
        "totals_right": sum(abs(got[k].total - want[k].total) < 0.005 for k in found),
        "counts_right": sum(got[k].payments == want[k].payments for k in found),
        "invented": len([k for k in got if k not in want]),
        "missing": [f"{want[k].payer} -> {want[k].payee}" for k in want if k not in got],
    }


# ---- what an agent is given to trace it with ---------------------------------------------------

RULES = ("You are LANTERN, the analysis workstation of the Economic Offences Wing, Kestrel Bay "
         "Police. Report only what the statements show. ")
KEEP_GOING = ("Do not write DONE while any payee you have reported has a statement on file "
              "that you have not opened. ")


def digest(file: str) -> dict[str, Any]:
    """Who one statement paid, by payee, with the number of payments and the total."""
    by: dict[str, list[float]] = {}
    for r in statement(file):
        if r["debit"]:
            by.setdefault(r["counterparty"], []).append(float(r["debit"]))
    return {"statement": file, "holder": holder_of(file), "paid_out_to": [
        {"payee": k, "payments": len(v), "total": f"{sum(v):.2f}"} for k, v in by.items()]}


def schema(name: str, description: str, **params: str) -> dict[str, Any]:
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "required": list(params),
                           "properties": {k: {"type": "string", "description": v}
                                          for k, v in params.items()}}}}


def listing(described: bool = True) -> tuple[str, dict[str, str]]:
    """The file list as the agent sees it, and the map from the names shown to the real files.

    Described: file, holder, account, bank and length. Bare: stmt-01.csv, stmt-02.csv, ...
    """
    rows = accounts()
    if described:
        shown = {a["file"]: a["file"] for a in rows}
        lines = [f"- {a['file']}: {a['holder']}, {a['account_no']}, {a['bank']}, "
                 f"{len(statement(a['file']))} lines." for a in rows]
    else:
        shown = {a["file"]: f"stmt-{i:02d}.csv" for i, a in enumerate(rows, 1)}
        lines = [f"- {shown[a['file']]}" for a in rows]
    return "Statements on file:\n" + "\n".join(lines), {v: k for k, v in shown.items()}


def tools(names: dict[str, str]) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    """Two tools over the statements: schemas, handlers, and the list of files opened."""
    opened: list[str] = []

    def money_out(file: str = "", **_: Any) -> dict[str, Any]:
        if file not in names:
            return {"failed": True, "error": f"No file named {file!r}.", "files": list(names)}
        opened.append(names[file])
        return {**digest(names[file]), "statement": file}

    def search_files(text: str = "", **_: Any) -> dict[str, Any]:
        hits = [shown for shown, real in names.items()
                if text.lower() in case.read(f"bank/{real}").lower()]
        return {"files_containing": hits}

    schemas = [
        schema("money_out", "Who one statement paid, with the number of payments and the total "
               "for each payee.", file="A file name from the list."),
        schema("search_files", "Which statements contain a text.",
               text="A name, account number or reference."),
    ]
    return schemas, {"money_out": money_out, "search_files": search_files}, opened


def unopened_payees(report: str, opened: list[str]) -> list[str]:
    """Payees named in a report's FLOW lines that have a statement on file nobody opened."""
    files = {a["holder"].lower(): a["file"] for a in accounts()}
    out = []
    for f in reported(report):
        file = files.get(f.payee.lower())
        if file and file not in opened and f.payee not in out and \
                f.payee != "Northwind Freight Ltd":
            out.append(f.payee)
    return out


def not_done(opened: list[str]):
    """A check for agent.run(until=...): the report is refused while a payee is unopened."""
    def check(report: str) -> str | None:
        left = unopened_payees(report, opened)
        if not left:
            return None
        return ("Not done. You reported payments to " + ", ".join(left) + ", which has a "
                "statement on file that you have not opened. Open it, follow the money on, and "
                "then give the whole report again, every FLOW line, ending with DONE.")
    return check
