"""Chapter 08 reference solution: a list the agent can choose from, and a check on what it chose."""

from __future__ import annotations


def listing(accounts: list[dict[str, str]], lengths: dict[str, int], described: bool = True
            ) -> tuple[str, dict[str, str]]:
    """The file list as the agent sees it, and the map from the names shown to the real files."""
    if described:
        shown = {a["file"]: a["file"] for a in accounts}
        lines = [f"- {a['file']}: {a['holder']}, {a['account_no']}, {a['bank']}, "
                 f"{lengths[a['file']]} lines." for a in accounts]
    else:
        shown = {a["file"]: f"stmt-{i:02d}.csv" for i, a in enumerate(accounts, 1)}
        lines = [f"- {shown[a['file']]}" for a in accounts]
    return "Statements on file:\n" + "\n".join(lines), {v: k for k, v in shown.items()}


def unopened(payees: list[str], accounts: list[dict[str, str]], opened: list[str]) -> list[str]:
    """Payees that have a statement on file which was not opened, each once, in order."""
    files = {a["holder"].lower(): a["file"] for a in accounts}
    out = []
    for payee in payees:
        file = files.get(payee.lower())
        if file and file not in opened and payee not in out:
            out.append(payee)
    return out
