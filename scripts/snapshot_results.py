"""Copy each chapter's recorded metrics to tests/fixtures/recorded-metrics.json.

`.progress/` is the learner's own and is not committed, so the tests read the build's recorded
runs from this copy: every challenge target must be one that the unchanged recorded run
misses (tests/test_learn.py). Run it after a chapter is run again and its README rewritten:
`uv run python scripts/snapshot_results.py`.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "recorded-metrics.json"


def main() -> int:
    snap = {}
    for path in sorted((ROOT / ".progress" / "results").glob("[0-9][0-9].json")):
        res = json.loads(path.read_text(encoding="utf-8"))
        snap[path.stem] = {"at": res["at"], "metrics": {
            k: v for k, v in res["metrics"].items() if isinstance(v, bool | int | float | str)}}
    OUT.write_text(json.dumps(snap, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(snap)} chapters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
