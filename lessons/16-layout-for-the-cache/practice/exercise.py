"""Chapter 16 exercise: lay a context out for the cache, and mark where each group ends.

Grade it with `make exercise N=16`. The tests pass in lists of sections, so no model is needed.
When it passes, `make lesson N=16 ARGS=--mine` runs the morning measurement and the 26
questions on your layout, and the hosted request puts its cache breakpoints where you said.
"""

from __future__ import annotations

from lantern.context import Section

# From the section that changes least to the one that changes most.
CHANGES = ("rarely", "weekly", "nightly", "per turn", "per question")
MAX_BREAKPOINTS = 4  # Anthropic takes at most four cache breakpoints in one request


def layout(parts: list[Section], changes: dict[str, str]) -> tuple[list[Section], list[int]]:
    """The sections ordered by how often they change, and where a cache breakpoint goes.

    `changes` maps each section's name to one of CHANGES.
    - Order the sections from the group that changes least to the group that changes most.
      Sections in the same group keep the order they were given in (a stable sort).
    - A breakpoint goes on the last section of every group except the last one present: the
      index, in the ordered list, of the last section before the group changes.
    - At most MAX_BREAKPOINTS breakpoints, the first ones kept.
    - A section whose name is missing from `changes`, or maps to a word not in CHANGES, is an
      error: raise ValueError naming it.
    - The list passed in is not changed.
    """
    # TODO 1: check every section's name has a frequency that is one of CHANGES.
    # TODO 2: sort a copy by CHANGES.index(changes[name]); Python's sort keeps ties in order.
    # TODO 3: collect i where the next section's frequency differs from this one's.
    # TODO 4: return the ordered sections and at most MAX_BREAKPOINTS of those indexes.
    raise NotImplementedError("write layout")
