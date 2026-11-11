"""Chapter 01 reference solution: read the input as the model does, as one sequence of lines."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def locate(parts: list[Any], phrase: str) -> list[tuple[int, str, str]]:
    """Every line of the flat input that contains `phrase`: (line number, section, line)."""
    found, n = [], 0
    for s in parts:
        for line in s.text.splitlines():
            n += 1
            if phrase in line:
                found.append((n, s.name, line.strip()))
    return found


def shares(parts: list[Any], count: Callable[[str], int]) -> dict[str, float]:
    """Each section's share of the whole input, as a fraction, by `count(text)`."""
    sizes = {s.name: count(s.text) for s in parts}
    total = sum(sizes.values())
    return {name: (size / total if total else 0.0) for name, size in sizes.items()}
