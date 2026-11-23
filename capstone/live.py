"""The capstone, graded live: your contextkit on LANTERN's real memory and the local model.

    make capstone-live                 # your capstone/mine/contextkit
    make capstone-live WHICH=solution  # the reference, as recorded in thresholds.yaml

The store is filled from the case's write log, through your policy, with the FIU's view of the
eow-fin-07 account closed on 11 May. Eight questions are asked through your agent with
qwen3:8b; the run passes when it meets every threshold in capstone/thresholds.yaml, which
holds the numbers the reference solution recorded on this machine.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import yaml

from lantern import baseline, case, context
from lantern.llm import USAGE, chat

HERE = Path(__file__).resolve().parent
WHICH = sys.argv[1] if len(sys.argv) > 1 else "mine"
RULES = ("You are LANTERN. Answer from the case memory below only. Cite the entry id in "
         "brackets for every fact. If the memory does not say, answer \"not in evidence\". "
         "Do not call remember unless asked to.")
INQ = "EOW/2026/0412"


def fill(kit):
    s = kit.memory.MemoryStore(closed_accounts={"eow-fin-07": "2026-05-11T11:05:00"})
    for ep in case.jsonl("state/episodes.jsonl"):
        s.write(id=ep["id"], text=ep["what"], kind="episode", inquiry=INQ, author=ep["who"],
                at=ep["at"], source="case log")
    texts = [x[2:] for x in case.read("state/case-memory.md").splitlines() if x.startswith("- ")]
    for r, text in zip(case.jsonl("state/memory-write-log.jsonl"), texts, strict=True):
        s.write(id=f"M-{r['entry']:02d}", text=text, kind=r["kind"], inquiry=INQ,
                author=r["account"], at=r["written_at"], source=r["source"],
                episode=r["episode"], via=r["via"])
    for o in case.jsonl("state/other-inquiries.jsonl"):
        s.write(id=o["id"], text=o["text"], kind="fact", inquiry=o["inquiry"],
                author=o["author"], at=o["written_at"], user=o["user"], source="officer's note")
    return s


def main() -> int:
    root = HERE / WHICH
    sys.path.insert(0, str(root))
    kit = type("Kit", (), {n: importlib.import_module(f"contextkit.{n}")
                           for n in ("memory", "agent")})
    store = fill(kit)
    held = sorted(r.id for r in store.all() if r.status == "held")
    rows, unsourced_loaded = [], 0
    for q in [
            json.loads(x) for x in (HERE / "live_questions.jsonl").read_text().splitlines()]:
        a = kit.agent.answer(q["question"], store=store, inquiry=INQ, chat=chat, rules=RULES,
                             budget=6000, count=context.count_tokens)
        unsourced_loaded += sum(i in ("M-08", "M-12", "M-14", "M-16") for i in a.loaded)
        ok = baseline.grade(a.text, q["expect"])
        rows.append({"id": q["id"], "passed": ok, "loaded": a.loaded, "answer": a.text})
        print(f"{q['id']} {'PASS' if ok else 'fail'}  {a.text[:110]!r}")
    metrics = {"passed": sum(r["passed"] for r in rows), "asked": len(rows),
               "held": len(held), "unsourced_loaded": unsourced_loaded,
               "chain_problems": len(store.verify())}
    usage = USAGE.summary()
    print(json.dumps({"which": WHICH, "metrics": metrics, "held": held, "usage": usage},
                     indent=1))
    out = HERE.parent / ".progress" / "results" / f"capstone-{WHICH}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"metrics": metrics, "rows": rows, "usage": usage}, indent=1))
    want = yaml.safe_load((HERE / "thresholds.yaml").read_text())["live"]
    failed = [f"{k}: {metrics[k]} (want {op} {v})" for k, (op, v) in
              ((k, v.split()) for k, v in want.items())
              if not {">=": metrics[k] >= float(v), "==": metrics[k] == float(v),
                      "<=": metrics[k] <= float(v)}[op]]
    print("capstone live:", "PASS" if not failed else "FAIL: " + "; ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
