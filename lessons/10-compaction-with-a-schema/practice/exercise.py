"""Chapter 10 exercise: the check that decides whether a compacted state is kept.

Grade it with `make exercise N=10`. The tests pass in forms and tool results, so no model is
needed. When it passes, `make lesson N=10 ARGS=--mine` checks every compaction with yours.
"""

from __future__ import annotations

from typing import Any

BANK_WORDS = ("Bank",)


def seen_flows(ledger: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Every payment to a payee that is not a bank, from the ledger, as the form writes it."""
    return [{"payer": d["holder"], "payee": p["payee"], "payments": p["payments"],
             "total": p["total"], "source": file}
            for file, d in ledger.items() for p in d["paid_out_to"]
            if not any(w in p["payee"] for w in BANK_WORDS)]


def check(state: dict[str, Any], ledger: dict[str, dict[str, Any]]) -> list[str]:
    """Problems with a filled-in form, against the ledger. An empty list means it is kept.

    `state` is {"flows": [{"payer", "payee", "payments", "total", "source"}],
    "accounts_read": [file], "open_questions": [text]}. `seen_flows(ledger)` is what the tools
    returned. Report, in this order:

    - "flow N has no payer, total"      a flow with an empty or absent field (N from 1); such
                                        a flow is then ignored
    - "missing: A paid B (file)"        a seen flow that the form does not hold
    - "A paid B: total X, the tool said Y"       a total that differs (compare as numbers:
                                                 "1,873,000.00" equals "1873000.00")
    - "A paid B: N payments, the tool said M"    a count that differs
    - "not in any tool result: A paid B"         a flow the tools never returned (a payee
                                                 that is a bank is let through)
    - "accounts_read leaves out x.csv, y.csv"    files in the ledger the form does not list
    """
    # TODO 1: index the seen flows and the form's complete flows by (payer, payee).
    # TODO 2: walk the seen flows: missing, wrong total, wrong count.
    # TODO 3: walk the form's flows: any the tools never returned.
    # TODO 4: accounts_read against the ledger's files.
    raise NotImplementedError("write check")
