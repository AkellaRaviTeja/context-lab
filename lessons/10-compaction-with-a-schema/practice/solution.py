"""Chapter 10 reference solution: the check that decides whether a compacted state is kept."""

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
    """Problems with a filled-in form, against the ledger. An empty list means it is kept."""
    problems = []
    want = {(f["payer"], f["payee"]): f for f in seen_flows(ledger)}
    got = {}
    for i, f in enumerate(state.get("flows", []), 1):
        missing = [k for k in ("payer", "payee", "payments", "total", "source") if not f.get(k)]
        if missing:
            problems.append(f"flow {i} has no {', '.join(missing)}")
            continue
        got[(f["payer"], f["payee"])] = f
    for key, f in want.items():
        g = got.get(key)
        if g is None:
            problems.append(f"missing: {key[0]} paid {key[1]} ({f['source']})")
        elif float(str(g["total"]).replace(",", "")) != float(f["total"]):
            problems.append(f"{key[0]} paid {key[1]}: total {g['total']}, the tool said "
                            f"{f['total']}")
        elif int(g["payments"]) != f["payments"]:
            problems.append(f"{key[0]} paid {key[1]}: {g['payments']} payments, the tool said "
                            f"{f['payments']}")
    for key in got:
        if key not in want and not any(w in key[1] for w in BANK_WORDS):
            problems.append(f"not in any tool result: {key[0]} paid {key[1]}")
    unread = sorted(set(ledger) - set(state.get("accounts_read", [])))
    if unread:
        problems.append(f"accounts_read leaves out {', '.join(unread)}")
    return problems
