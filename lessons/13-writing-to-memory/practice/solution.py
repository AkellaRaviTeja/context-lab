"""Chapter 13 reference solution: the write gate."""

from __future__ import annotations

import re
from collections.abc import Iterable

from lantern.memory import Entry, Policy, Store, default_policy

JUDGEMENT = re.compile(r"\b(cleared|licensed|routine|ordinary|need no|do not)\b", re.I)
FIGURE = re.compile(r"\b\d[\d,]*\.\d{2}\b|\b[A-Z]{2,}(?:-[A-Z0-9]+)+\b")


def figures(text: str) -> list[str]:
    """Amounts (296,400.00) and references (ICB-77-10458) in a text, commas taken out."""
    return [f.replace(",", "") for f in FIGURE.findall(text)]


def write_gate(read: dict[str, str] | None = None, *,
               machine_accounts: Iterable[str] = ("svc-lantern-sync",),
               inactive: dict[str, str] | None = None,
               models: Iterable[str] = ("lantern",)) -> Policy:
    """The write policy: default_policy, then the model's citations, then judgements."""
    base = default_policy(machine_accounts, inactive)
    docs = read if read is not None else {}  # the session adds to it as it reads
    model_authors = set(models)

    def policy(entry: Entry, store: Store) -> list[str]:
        problems = base(entry, store)
        if entry.author in model_authors:
            cited = [name for name in docs if name.lower() in (entry.source or "").lower()]
            if not cited:
                problems.append("cites no document read in this session")
            else:
                shown = " ".join(docs[n] for n in cited).replace(",", "")
                missing = [f for f in figures(entry.text) if f not in shown]
                if missing:
                    problems.append(f"the source does not show {', '.join(missing)}")
        found = JUDGEMENT.findall(entry.text)
        if found:
            problems.append(f"a judgement ({found[0].lower()}): a person must keep it")
        return problems
    return policy
