"""The capstone's tests run against `capstone/solution/contextkit` (make test) or against the
learner's own `capstone/mine/contextkit` (make capstone, CAPSTONE=mine)."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"


def kit_root() -> Path:
    return HERE / ("mine" if os.getenv("CAPSTONE") == "mine" else "solution")


@pytest.fixture(scope="session")
def kit():
    root = kit_root()
    if not (root / "contextkit" / "__init__.py").exists():
        pytest.fail(f"{root / 'contextkit'} does not exist yet: create it (capstone/README.md)")
    for name in [m for m in sys.modules if m == "contextkit" or m.startswith("contextkit.")]:
        del sys.modules[name]
    sys.path.insert(0, str(root))
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    mods = {n: importlib.import_module(f"contextkit.{n}") for n in ("memory", "builder", "agent")}
    sys.path.remove(str(root))
    return type("Kit", (), mods)
