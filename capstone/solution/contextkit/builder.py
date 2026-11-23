"""A context builder: sections in a stable-first layout, inside a token budget, versioned."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Section:
    name: str
    text: str
    stable: bool = False  # the same on every request: goes first, so a prefix cache can hold it
    priority: int = 0  # over budget, the lowest priority is dropped first
    required: bool = False  # never dropped (the rules, the question)


@dataclass
class Built:
    text: str
    order: list[str]
    dropped: list[str] = field(default_factory=list)
    tokens: int = 0
    version: str = ""
    stable_version: str = ""


class OverBudget(Exception):
    pass


def build(sections: list[Section], *, budget: int, count: Callable[[str], int]) -> Built:
    """Stable sections first, in the order given, then the rest in the order given. Over the
    budget, drop optional sections, lowest priority first, and say which. If the required
    sections alone do not fit, raise OverBudget: never cut the rules or the question."""
    kept = [s for s in sections if s.stable] + [s for s in sections if not s.stable]
    dropped: list[str] = []

    def size(parts: list[Section]) -> int:
        return count("\n\n".join(s.text for s in parts))

    while size(kept) > budget:
        optional = [s for s in kept if not s.required]
        if not optional:
            raise OverBudget(f"the required sections need {size(kept)} tokens; the budget is "
                             f"{budget}")
        worst = min(optional, key=lambda s: s.priority)
        kept.remove(worst)
        dropped.append(worst.name)
    text = "\n\n".join(s.text for s in kept)
    stable = "\n\n".join(s.text for s in kept if s.stable)
    return Built(text=text, order=[s.name for s in kept], dropped=dropped, tokens=size(kept),
                 version=hashlib.sha256(text.encode()).hexdigest()[:12],
                 stable_version=hashlib.sha256(stable.encode()).hexdigest()[:12])
