"""Fail if any text file in the repository contains an em dash or en dash.

Recorded model output is left out: it is evidence, and evidence is not edited to suit a style
rule. A model that writes a dash in a report has written a dash.
"""

from __future__ import annotations

import fnmatch
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANNED = {chr(0x2014): "em dash", chr(0x2013): "en dash"}
SKIP = {".venv", "node_modules", ".git", ".sandbox", ".scratch", "output", "screenshots"}
# Files that hold what a model wrote, word for word.
RECORDED = ("results/*/records.jsonl", "results/attacks/*.jsonl", "case/runs/R-*.json",
            "results/conversations/*.jsonl",
            "case/sessions/sessions.jsonl", "case/labels/absence-runs.jsonl")


def recorded(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return any(fnmatch.fnmatch(rel, pattern) for pattern in RECORDED)


def main() -> int:
    files = [p for ext in ("*.md", "*.py", "*.yaml", "*.yml", "*.html", "*.d2", "*.txt", "*.csv",
                           "*.jsonl", "*.ts", "*.json")
             for p in ROOT.rglob(ext) if not SKIP & set(p.relative_to(ROOT).parts)]
    kept = sum(1 for p in files if recorded(p))
    files = [p for p in files if not recorded(p)]
    problems = []
    for path in files:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for ch, name in BANNED.items():
                if ch in line:
                    problems.append(f"{path.relative_to(ROOT)}:{n}: {name}")
    print("\n".join(problems))
    print(f"prose: checked {len(files)} files, {len(problems)} problems "
          f"({kept} files of recorded model output left as written)")
    return 1 if problems or not files else 0


if __name__ == "__main__":
    sys.exit(main())
