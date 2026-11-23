"""Chapter 13 exercise: the write gate, the policy every new memory passes through.

Grade it with `make exercise N=13`. The tests write entries into a `lantern.memory.Store` with
your policy, so no model is needed. When it passes, `make lesson N=13 ARGS=--mine` replays the
case memory, and LANTERN's own `remember` calls, through yours.
"""

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
    """Return a policy: a function (entry, store) -> the list of problems; empty means keep.

    1. Every problem `default_policy(machine_accounts, inactive)` finds: no source and no
       episode, a machine account's route, an account written after it was closed.
    2. When the author is one of `models`, the source must name a document in `read` (a name
       from `read` appearing in `entry.source`, ignoring case). If none does, the problem is
       exactly "cites no document read in this session".
    3. When it does, every figure in the text (see `figures`) must be in the cited documents
       (commas taken out). If any is not: "the source does not show <figures, comma-joined>".
    4. For any author: if the text passes a judgement (JUDGEMENT matches), add
       "a judgement (<the first word matched, lower case>): a person must keep it".
    """
    # TODO 1: build the base policy, and keep `read` itself, not a copy: a session adds each
    #         document to it as it reads, after the policy was made.
    # TODO 2: define policy(entry, store) that starts from the base policy's problems.
    # TODO 3: add the citation and figure checks for the model's own entries.
    # TODO 4: add the judgement check, then return the problems; return policy.
    raise NotImplementedError("write write_gate")
