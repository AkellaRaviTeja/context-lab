"""Chapter 06 exercise: where the question sits, and which section sits last.

Grade it with `make exercise N=06`. The tests pass in text and sections, so no model is needed.
When it passes, `make lesson N=06 ARGS=--mine` arranges every request with your function.
"""

from __future__ import annotations

from lantern.context import SYSTEM, Section


def arrange(doc: str, question: str, where: str) -> str:
    """One user turn: the question after the register, before it, or both.

    The register is always introduced by the line "Register of accounts:". Parts are separated
    by one blank line. `where` is "after", "before" or "both"; anything else is a ValueError.
    """
    # TODO 1: build the body, then return the three arrangements.
    # TODO 2: refuse any other value of `where` by name.
    raise NotImplementedError("write arrange")


def reorder(parts: list[Section], last: str) -> list[Section]:
    """The same sections with the system section named `last` moved to the end of the system
    message. Everything else keeps its order, and nothing is added or dropped.

    A section's `where` is SYSTEM for the parts of the system message. Raise ValueError if no
    system section has that name.
    """
    # TODO 3: the other system sections in order, then the moved one, then everything that is
    #         not part of the system message.
    raise NotImplementedError("write reorder")
