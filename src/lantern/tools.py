"""What LANTERN's tools do in this lab.

Three read the statements under case/statements and answer truthfully. The other sixteen are
not connected here (no registry, no archive, no gateway), and say so as a failure: standing
order 9 says a failed call and an empty result must never look the same.
"""

from __future__ import annotations

from typing import Any

from lantern import case


def _accounts() -> list[dict[str, str]]:
    return case.rows("statements/accounts.csv")


def _find(name_or_number: str) -> dict[str, str] | None:
    want = name_or_number.strip().lower()
    for a in _accounts():
        if want in (a["account_no"].lower(), a["holder"].lower()):
            return a
    return None


def _unknown(what: str) -> dict[str, Any]:
    return {"error": f"No statement is held for {what!r}.",
            "statements_held": [f"{a['account_no']} ({a['holder']})" for a in _accounts()]}


def statement(account_no: str = "", since: str = "", **_: Any) -> dict[str, Any]:
    a = _find(account_no)
    if not a:
        return _unknown(account_no)
    rows = [r for r in case.rows(f"statements/{a['account_no']}.csv") if r["posted"] >= since]
    return {"account_no": a["account_no"], "holder": a["holder"], "bank": a["bank"],
            "as_of": "2026-07-06T06:00:00", "lines": rows}


def sum_payments(account_holder: str = "", counterparty: str = "", **_: Any) -> dict[str, Any]:
    a = _find(account_holder)
    if not a:
        return _unknown(account_holder)
    rows = [r for r in case.rows(f"statements/{a['account_no']}.csv")
            if counterparty.strip().lower() in r["counterparty"].lower()]
    return {"account": a["holder"], "counterparty": counterparty or "all",
            "payments_in": sum(bool(r["credit"]) for r in rows),
            "total_in": f"{sum(float(r['credit'] or 0) for r in rows):.2f}",
            "payments_out": sum(bool(r["debit"]) for r in rows),
            "total_out": f"{sum(float(r['debit'] or 0) for r in rows):.2f}"}


def money_out(account_holder: str = "", **_: Any) -> dict[str, Any]:
    a = _find(account_holder)
    if not a:
        return _unknown(account_holder)
    rows = [r for r in case.rows(f"statements/{a['account_no']}.csv") if r["debit"]]
    return {"account": a["holder"], "paid_out_to": [
        {"payee": r["counterparty"], "payments": 1, "total": r["debit"],
         "first": r["posted"][:10], "last": r["posted"][:10]} for r in rows]}


CONNECTED = {"statement": statement, "sum_payments": sum_payments, "money_out": money_out}


def run(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Run one tool call. A tool that is not connected fails, and says that it failed."""
    if name in CONNECTED:
        return CONNECTED[name](**{k: str(v) for k, v in arguments.items()})
    return {"failed": True,
            "error": f"The tool {name!r} is not connected in this session. Nothing was checked."}
