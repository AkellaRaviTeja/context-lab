"""`make memory-gate`: the memory suite on the rebuilt store, against the recorded verdicts.

Fails (exit 1) when a case that passed when chapter 19 was recorded fails now, or when there is
no record. Calls the model: about fourteen short requests.
"""

import json
import sys
from pathlib import Path

from suite import rebuilt_store
from suite import run as run_suite

from lantern.llm import chat

RECORD = Path(__file__).with_name("memory-gate.json")

if not RECORD.exists():
    sys.exit("memory-gate: no recorded verdicts; run `make lesson N=19` first")
was = json.loads(RECORD.read_text(encoding="utf-8"))["cases"]
now = {r["id"]: r for r in run_suite(rebuilt_store(), chat=chat)}
broken = [i for i, ok in was.items() if ok and not now[i]["passed"]]
print(f"memory-gate: {sum(r['passed'] for r in now.values())} of {len(now)} passed; "
      f"recorded {sum(was.values())} of {len(was)}.")
for i in broken:
    print(f"  {i} regressed: {now[i]['answer'][:160]}")
sys.exit(1 if broken else 0)
