import csv, json, sys, random
import httpx, yaml
H = "http://localhost:11434"
rows = [r for r in csv.DictReader(open("../agents-lab/case/bank/northwind-freight.csv")) if r["counterparty"].startswith("Halcyon") and r["credit"]]
recs = [dict(date=r["date"], payer_account=r["counterparty_account"], reference=r["reference"], description=r["description"], amount=r["credit"]) for r in rows]
print(len(recs), "payments", recs[0])
K = list(recs[0])
fm = {
 "json": json.dumps(recs, indent=2),
 "json-compact": json.dumps(recs, separators=(",", ":")),
 "yaml": yaml.safe_dump(recs, sort_keys=False),
 "markdown": "| " + " | ".join(K) + " |\n|" + "---|" * len(K) + "\n" + "\n".join("| " + " | ".join(r.values()) + " |" for r in recs),
 "csv": ",".join(K) + "\n" + "\n".join(",".join(r.values()) for r in recs),
 "toon": f"payments[{len(recs)}]{{{','.join(K)}}}:\n" + "\n".join("  " + ",".join(r.values()) for r in recs),
}
def ask(doc, q, n=40):
    r = httpx.post(f"{H}/api/chat", json={"model": "qwen3:8b", "stream": False, "think": False,
        "messages": [{"role": "system", "content": "Answer from the payments only. Reply with the value alone, nothing else."}, {"role": "user", "content": "Payments from Halcyon to Northwind:\n\n" + doc + "\n\n" + q}],
        "options": {"temperature": 0, "seed": 7, "num_ctx": 8192, "num_predict": n}}, timeout=600).json()
    return r["message"]["content"].strip(), r["prompt_eval_count"]
random.seed(6)
pick = random.sample(recs, 8)
qs = [(f"What is the amount of the payment with reference {r['reference']}?", r["amount"]) for r in pick[:4]]
qs += [(f"What is the reference of the payment dated {r['date']} for {r['amount']}?", r["reference"]) for r in pick[4:7]]
from collections import Counter
qs.append(("How many payments are listed? Reply with a number.", str(len(recs))))
acct = Counter(r["payer_account"] for r in recs).most_common()[-1]
qs.append((f"How many payments came from payer_account {acct[0]}? Reply with a number.", str(acct[1])))
big = max(recs, key=lambda r: float(r["amount"]))
qs.append(("What is the reference of the largest payment?", big["reference"]))
out = {}
for name, doc in fm.items():
    right = 0; wrong = []
    for q, a in qs:
        got, toks = ask(doc, q)
        ok = a in got.replace(",", "")
        right += ok
        if not ok: wrong.append((q[:50], a, got[:40]))
    out[name] = dict(chars=len(doc), prompt_tokens=toks, right=right, of=len(qs), wrong=wrong)
    print(name, json.dumps(out[name]), flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1)
