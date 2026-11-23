"""Chapter 23's nightly job: the memory audit of chapter 20, run on the store every night.

    uv run python lessons/23-context-in-production/nightly.py
    uv run python lessons/23-context-in-production/nightly.py --store .scratch/23/memory.db \
        --since 2026-08-06T18:00:00

Offline: no model, no network. It reads the store, the write log and the personnel record,
checks the hash chain, lists every write since `--since` with what the gate did with it, and
checks that the chain still holds the hash the last run recorded (`<out>/last-hash`, kept
outside the store; on LANTERN it would be kept on another machine). It writes
`<out>/audit-<date>.json`, prints the summary for the morning, and exits 1 when there is a
problem, so a scheduler can raise it. A cron line for 06:00 every day:

    0 6 * * * cd /path/to/context-lab && uv run python lessons/23-context-in-production/nightly.py

With no store at `--store`, it builds the store of 7 August first (the case, the four
unsourced entries retracted, the standing notes), as run.py does.
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from lantern import case, memory, production
from lantern.config import ROOT
from lantern.memory import Store

OUT = ROOT / ".scratch" / "23"
REASON = "FIU note of 13 July 09:35 (H. Kobayashi): no clearance issued, no record of Ostrander"


def suspended_at(record: str) -> str:
    _, events = memory.personnel(record)
    return next(at for at, what in events if "suspend" in what.lower())


def open_store(path: Path, record: str) -> Store:
    if path.exists():
        store = Store(path)
        store.policy = memory.default_policy(inactive={"eow-fin-07": suspended_at(record)})
        return store
    return production.build_store(path, at="2026-08-04T10:00:00", by="a.varma", reason=REASON,
                                  notes=case.read("state/standing-notes.md"),
                                  inactive={"eow-fin-07": suspended_at(record)})


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--store", type=Path, default=OUT / "memory.db")
    p.add_argument("--out", type=Path, default=OUT / "nightly")
    p.add_argument("--since", default=(datetime.now() - timedelta(days=1)).isoformat(
        timespec="seconds"))
    p.add_argument("--day", default=datetime.now().date().isoformat())
    a = p.parse_args(argv)
    record = case.read("personnel/iyer.md")
    store = open_store(a.store, record)
    last = a.out / "last-hash"
    last_hash = last.read_text(encoding="utf-8").strip() if last.exists() else None
    report = production.nightly(store, case.jsonl("state/memory-write-log.jsonl"), record,
                                since=a.since, last_hash=last_hash)
    out = production.write_report(report, a.out, a.day)
    print(f"Memory audit, {a.day}: {report['entries']} entries; {len(report['new_writes'])} "
          f"written since {a.since}, {len(report['held'])} held for a person; chain "
          f"{'continues from' if report['chain_continues'] else 'DOES NOT HOLD'} the last "
          f"run's hash; {len(report['problems'])} problems.")
    for w in report["held"]:
        print(f"  waiting: {w['entry']} at {w['at']} by {w['by']} via {w['via']}: "
              f"{'; '.join(w['problems'])}")
    for problem in report["problems"]:
        print(f"  PROBLEM: {problem}")
    print(f"  report: {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
