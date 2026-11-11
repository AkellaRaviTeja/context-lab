"""Chapter 01 exercise: read the input as the model does, as one sequence of lines.

Grade it with `make exercise N=01`. The tests pass in sections (objects with `.name` and
`.text`) and a counting function, so no model is needed. When it passes,
`make lesson N=01 ARGS=--mine` prints LANTERN's input with your functions.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def locate(parts: list[Any], phrase: str) -> list[tuple[int, str, str]]:
    """Every line of the flat input that contains `phrase`: (line number, section, line).

    The flat input is every section's lines, one section after another, in the order given.
    Line numbers start at 1 and run on from one section to the next, because the model reads
    one sequence and does not see where a section ends. The line is returned stripped.
    """
    # TODO 1: walk the sections in order and their text line by line (`str.splitlines`),
    #         keeping one running line number across all of them.
    # TODO 2: when a line contains the phrase, keep (number, section name, stripped line).
    raise NotImplementedError("write locate")


def shares(parts: list[Any], count: Callable[[str], int]) -> dict[str, float]:
    """Each section's share of the whole input, as a fraction, by `count(text)`.

    `count` is the tokenizer: it takes a text and returns its size. Do not measure by `len`.
    An empty input gives every section a share of 0.0.
    """
    # TODO 3: size each section with `count`, add the sizes up, divide.
    # TODO 4: if the total is zero, every share is 0.0 (no division by zero).
    raise NotImplementedError("write shares")
