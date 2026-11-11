"""Spike: what does Ollama's prefix reuse save, and does prompt_eval_count change?"""
import csv, json, sys, time
import httpx
H = "http://localhost:11434"
rows = list(csv.DictReader(open("../agents-lab/case/bank/arden-logistics.csv")))
doc = "\n".join(",".join(r.values()) for r in rows[:55])
SYS = "You are LANTERN. Cite evidence or say 'not in evidence'. Answer in one short line."
def ask(messages, label):
    t = time.time()
    r = httpx.post(f"{H}/api/chat", json={"model": "qwen3:8b", "messages": messages, "stream": False, "think": False,
        "options": {"temperature": 0, "seed": 7, "num_ctx": 8192, "num_predict": 20}}, timeout=600).json()
    out = dict(label=label, prompt_tokens=r.get("prompt_eval_count"), prompt_s=round(r.get("prompt_eval_duration", 0) / 1e9, 3),
               load_s=round(r.get("load_duration", 0) / 1e9, 3), eval_s=round(r.get("eval_duration", 0) / 1e9, 3), wall_s=round(time.time() - t, 2))
    print(json.dumps(out), flush=True)
    return out
def msgs(head, tail_q, stamp_top=""):
    return [{"role": "system", "content": stamp_top + head}, {"role": "user", "content": doc + "\n\n" + tail_q}]
res = []
for rnd in range(3):
    res.append(ask(msgs(SYS, f"Round {rnd}: cold start filler {time.time()}"), "evict (different doc order)") if False else ask([{"role": "user", "content": f"unrelated {rnd} {time.time()}: say ok"}], "other conversation (evicts)"))
    head = SYS + f" Session {rnd}-{time.time()}."
    res.append(ask(msgs(head, "How many rows mention Corvane?"), "cold"))
    res.append(ask(msgs(head, "How many rows mention Corvane?"), "exact repeat"))
    res.append(ask(msgs(head, "What is the first date in the statement?"), "same prefix, new question at end"))
    res.append(ask(msgs(head, "What is the last date in the statement?", stamp_top=f"Time now: {time.time()}. "), "timestamp at the top"))
    res.append(ask(msgs(head, "What is the largest debit?", stamp_top=f"Time now: {time.time()}. "), "timestamp at the top, again"))
    res.append(ask([{"role": "user", "content": f"unrelated b{rnd} {time.time()}: say ok"}], "other conversation in between"))
    res.append(ask(msgs(head, "What is the largest credit?", stamp_top=""), "same prefix after the other conversation"))
json.dump(res, open(sys.argv[1], "w"), indent=1)
