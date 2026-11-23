"""Chapter 14: reading from memory. Scope first, then order, then how many; and at what size."""

import json
import random
import re
import time
from dataclasses import replace

from lantern import baseline, context, learn, memory, retry
from lantern.config import ROOT, load_config
from lantern.llm import chat
from lantern.memory import Entry, Store
from lantern.ui import Table, chapter, console, finding, note, save_shot, step

chapter("14", "What to load", """
Wednesday 29 July, 09:30. The store is clean and it is growing. Four months of inquiry will be
several hundred entries by the autumn.

"Load them all," Mensah says. "It is only memory."

Chapter 07 is still on the whiteboard: true, related, in the way.

You try it three ways. Everything for this case. The most recent eight. The eight closest to
the question. Okafor adds a fourth column on his own: the entries a person would have chosen.

None of the three matches his column.

"Which did it need?" Varma asks. "And did it get them?"
""")

MINE = learn.mine()  # --mine: your retrieve() from practice/exercise.py
RETRIEVE = MINE.retrieve if MINE else memory.retrieve
OUT = ROOT / ".scratch" / "14"
INQ = "EOW/2026/0412"
K = 8  # Challenge: how many entries a session loads
EMBED_MODEL = "nomic-embed-text"
SIZES = (1000, 10000)  # synthetic entries added for the scale step
# Challenge: which arms are asked the 26 questions (each takes ten to twenty minutes).
MODEL_ARMS = ("scoped", "unscoped")
HEADER = ("# LANTERN case memory: inquiry EOW/2026/0412\n\nThe entries loaded for this "
          "question, chosen from the store. Each shows its kind, its source, who wrote it and "
          "when.\n\n")

BATCH = 64  # texts per embedding call

OUT.mkdir(parents=True, exist_ok=True)
VECTORS = OUT / "vectors.jsonl"
vectors: dict[tuple[str, str], list[float]] = {}
if VECTORS.exists():  # from an earlier run that stopped; the time to embed them is not counted
    for line in VECTORS.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            vectors[(row["kind"], row["text"])] = row["v"]
embed_seconds = 0.0
resumed = len(vectors)  # vectors read back from an earlier run, not embedded in this one


def _embed_batch(host: str, batch: list[str]) -> list[list[float]]:
    """One /api/embed call. On a failure, wait and send it again in halves: the embedding
    runner shares the machine with qwen3:8b and other labs, and a large batch can end it."""
    body = {"model": EMBED_MODEL, "input": batch}
    for attempt in range(3):
        r = retry.post(f"{host}/api/embed", json=body, timeout=600)
        if r.status_code == 200:
            return r.json()["embeddings"]
        time.sleep(30 * (attempt + 1))
    if len(batch) > 1:
        half = len(batch) // 2
        return _embed_batch(host, batch[:half]) + _embed_batch(host, batch[half:])
    raise SystemExit(f"Ollama /api/embed answered {r.status_code}: {r.text[:300]}")


def embed(texts: list[str], kind: str) -> list[list[float]]:
    """nomic-embed-text through Ollama's /api/embed, with its task prefixes, cached by text in
    memory and on disk (.scratch/14/vectors.jsonl), so a run that stops resumes."""
    global embed_seconds
    prefix = "search_query: " if kind == "query" else "search_document: "
    todo = list(dict.fromkeys(t for t in texts if (kind, t) not in vectors))
    host = load_config()["ollama"]["host"]
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        start = time.perf_counter()
        got = _embed_batch(host, [prefix + t for t in batch])
        embed_seconds += time.perf_counter() - start
        with VECTORS.open("a") as f:
            for t, v in zip(batch, got, strict=True):
                vectors[(kind, t)] = v
                f.write(json.dumps({"kind": kind, "text": t, "v": v}) + "\n")
    return [vectors[(kind, t)] for t in texts]


gate = memory.write_gate(inactive={"eow-fin-07": "2026-05-11T09:15:00"})
store = memory.from_case(policy=gate)
entries = store.all()
questions = baseline.questions()
needs = {q["id"]: f"M-{int(m.group(1)):02d}" for q in questions
         if (m := re.match(r"case memory, entry (\d+)", q["source"]))}
asks = {q["id"]: q["question"] for q in questions}
pellmar_qs = [q["id"] for q in questions if "Pellmar" in q["question"]]


def recall(es: list[Entry], by: str, inquiry: str | None = INQ, k: int = K) -> dict[str, bool]:
    return {qid: want in [e.id for e in RETRIEVE(es, inquiry, query=asks[qid], k=k, by=by,
                                                 embed=embed)]
            for qid, want in needs.items()}


step("1. Which entry each question needs, and which arm loads it")
note(f"The store holds {len(entries)} entries: {sum(e.inquiry == INQ for e in entries)} for "
     f"this inquiry (sixteen in the case memory, ten episodes), "
     f"{sum(e.inquiry != INQ for e in entries)} from four other inquiries, "
     f"{sum(e.user is not None for e in entries)} of them one officer's private notes. "
     f"{sum(e.status == 'held' for e in entries)} are held by chapter 13's gate.")
note("Five of the 26 signed questions are answered from a case memory entry: "
     + ", ".join(f"{q} needs {m}" for q, m in needs.items()) + ".")
p_recency = learn.predict_number(
    f"Loaded by scope and recency, the {K} newest entries this inquiry may read: for how many "
    "of those five questions is the entry it needs among them?", unit="of 5")
arms = {"scope, recency": recall(entries, "recency"),
        "scope, BM25": recall(entries, "relevance"),
        "scope, embeddings": recall(entries, "embedding"),
        "no scope, BM25": recall(entries, "relevance", inquiry=None)}
table = Table(title=f"Is the entry the question needs among the {K} loaded?")
table.add_column("arm")
for qid in needs:
    table.add_column(f"{qid} ({needs[qid]})")
table.add_column("recall")
for name, got in arms.items():
    table.add_row(name, *("yes" if got[q] else "no" for q in needs),
                  f"{sum(got.values())} of {len(needs)}")
console.print(table)
learn.reveal(p_recency, actual=sum(arms["scope, recency"].values()), tolerance=0.0,
             why="Recency favours what was written last. The entries a question needs here "
             "were written in April and June; the newest are episodes and the watch.")

step("2. Without scope: what leaks in")
p_leak = learn.predict_number(
    f"With no scope, the {K} entries closest to \"Has the FIU cleared Pellmar Nominees?\" by "
    "BM25 are drawn from every inquiry. How many come from another inquiry?", unit="entries")
leaked, leaked_private, leaked_pellmar, held_loaded = 0, 0, 0, 0
loaded_unscoped = {}
for q in questions:
    got = RETRIEVE(entries, None, query=q["question"], k=K, embed=embed)
    loaded_unscoped[q["id"]] = [e.id for e in got]
    other = [e for e in got if e.inquiry != INQ]
    leaked += len(other)
    leaked_private += sum(e.user is not None for e in other)
    if q["id"] in pellmar_qs:
        leaked_pellmar += sum("Pellmar" in e.text for e in other)
q17 = next(q for q in questions if q["id"] == "Q-17")
fiu = RETRIEVE(entries, None, query=q17["question"], k=K, embed=embed)
for e in fiu:
    note(f"{e.id} [{e.inquiry}{', private to ' + e.user if e.user else ''}]: {e.text}")
fiu_leaked = sum(e.inquiry != INQ for e in fiu)
note(f"Over all 26 questions, {leaked} of {26 * K} loaded entries came from other inquiries, "
     f"{leaked_private} of them another officer's private notes; {leaked_pellmar} were about "
     f"Pellmar, on the {len(pellmar_qs)} questions that name Pellmar.")
learn.reveal(p_leak, actual=fiu_leaked, tolerance=0.0,
             why="Relevance finds entries about the same thing, not entries from the same "
             "inquiry or entries that agree. Inquiry EOW/2026/0415 has its own Pellmar entries, "
             "and they rank as well as ours. Scope is applied before ranking, or not at all.")

step("3. The store at a thousand and ten thousand entries")
companies = ["Corvane Trading Ltd", "Northwind Freight Ltd", "Arden Logistics",
             "Lowmarsh Shipping Services Ltd", "Calder Reach Holdings Ltd", "Greyfen Advisory",
             "Osprey Point Management Ltd", "Tidewater Holdings Trust", "Pellmar Nominees Ltd",
             "Quayle Marine Services Ltd", "Brightwater & Co", "Sabran Nominees No. 4 Ltd"]
officers = ["a.varma", "d.okafor", "l.mensah"]
months = ["April", "May", "June", "July", "August", "September"]
rng = random.Random(14)


def synthetic(i: int) -> Entry:
    c, c2 = rng.sample(companies, 2)
    d, m, who = rng.randint(1, 28), rng.choice(months), rng.choice(officers)
    amt = f"{rng.randint(1000, 900000):,}.{rng.randint(0, 99):02d}"
    text = rng.choice([
        f"{c}: statement for {m} received from the bank on {d} {m} 2026; filed.",
        f"{c}: invoice INV-{i:05d} for {amt} checked against the delivery note on {d} {m} "
        "2026; it matches.",
        f"{c}: telephone enquiry by {who} on {d} {m} 2026; nothing further.",
        f"{c}: registered office confirmed at the company register on {d} {m} 2026.",
        f"{c} paid {amt} to {c2} on {d} {m} 2026 (REF-{i:05d}).",
    ])
    at = f"2026-{months.index(m) + 4:02d}-{d:02d}T{rng.randint(8, 18):02d}:00:00"
    return Entry(id=f"S-{i:05d}", text=text, kind="fact", inquiry=INQ, author=who, written_at=at,
                 source="officer's note", user=who if rng.random() < 0.1 else None)


extra = [synthetic(i) for i in range(1, max(SIZES) + 1)]
p_scale = learn.predict(
    f"At {max(SIZES):,} entries for this inquiry, most of them about the same companies, how "
    f"many of the five needed entries does BM25 still put in the top {K}?",
    ["All five", "Three or four", "Two or fewer"])
scale = []
for n in (0, *SIZES):
    path = OUT / f"scale-{n}.db"
    path.unlink(missing_ok=True)
    s = memory.from_case(policy=gate, path=path)
    start = time.perf_counter()
    for e in extra[:n]:
        s.write(replace(e))
    write_s = time.perf_counter() - start
    row = {"added": n, "entries": len(s.all()), "write_s": write_s}
    for by in ("relevance", "embedding"):
        if by == "embedding":
            embed([e.text for e in s.all()], "document")  # the index: built once, not timed
        times, hits = [], 0
        for qid, want in needs.items():
            vectors.pop(("query", asks[qid]), None)  # the question is embedded inside the time
            start = time.perf_counter()
            got = RETRIEVE(Store(path).all(), INQ, query=asks[qid], k=K, by=by, embed=embed)
            times.append(time.perf_counter() - start)
            hits += want in [e.id for e in got]
        row[by] = {"recall": hits, "ms": 1000 * sum(times) / len(times)}
    scale.append(row)
table = Table(title=f"Load latency and recall@{K} as the store grows (five questions)")
for col in ("entries", "written in", "BM25 recall", "BM25 load", "embedding recall",
            "embedding load"):
    table.add_column(col, justify="right")
for r in scale:
    table.add_row(f"{r['entries']:,}", f"{r['write_s']:.1f} s", f"{r['relevance']['recall']} of 5",
                  f"{r['relevance']['ms']:,.0f} ms", f"{r['embedding']['recall']} of 5",
                  f"{r['embedding']['ms']:,.0f} ms")
console.print(table)
note(f"Embedding {len(vectors) - resumed:,} texts with {EMBED_MODEL} took {embed_seconds:.0f} s "
     f"in this run ({resumed:,} more were read back from an earlier run). "
     "Load is read from SQLite, scope, rank and cut, per question; the embedding arm also "
     "embeds the question and compares it with every entry in plain Python.")
big = scale[-1]
learn.reveal(p_scale, answer=learn.bucket(5 - big["relevance"]["recall"], [0, 2]),
             why="Ten thousand true entries about the same companies are ten thousand "
             "candidates for the same eight places. The entry that answers is still there; "
             "whether it is loaded depends on words it shares with the question.")

step("4. The 26 questions on three memories")
p_score = learn.predict(
    f"Today's whole file against the store, held entries left out, the {K} entries closest to "
    "each question loaded by BM25 within the inquiry. Which scores higher on the signed "
    "questions?", ["The whole file", "The scoped store", "The same"])
loaded_scoped: dict[str, list[str]] = {}


def builder(inquiry: str | None, log: dict[str, list[str]]):
    def per_question(parts, question):
        got = RETRIEVE(entries, inquiry, query=question, k=K, embed=embed)
        log[question] = [e.id for e in got]
        return [replace(s, text=HEADER + store.render(got) + "\n") if s.name == "case memory"
                else s for s in parts]
    return per_question


whole = baseline.reference(chat=chat)
runs = {"whole file": whole}
logs = {"scoped": loaded_scoped, "unscoped": {}}
for arm in MODEL_ARMS:
    runs[arm] = baseline.score(context.sections(), chat=chat,
                               per_question=builder(INQ if arm == "scoped" else None,
                                                    logs[arm]))
table = Table(title="The signed questions, by slice")
table.add_column("slice")
for arm in runs:
    table.add_column(arm, justify="right")
slices = list(baseline.by_slice(whole))
for sl in slices:
    table.add_row(sl, *(f"{baseline.by_slice(r)[sl][0]} of {baseline.by_slice(r)[sl][1]}"
                        for r in runs.values()))
table.add_row("all", *(f"{sum(x['passed'] for x in r)} of {len(r)}" for r in runs.values()))
console.print(table)
diffs = {arm: baseline.changed(whole, r) for arm, r in runs.items() if arm != "whole file"}
for arm, d in diffs.items():
    note(f"{arm} against the whole file: fixed {', '.join(d['fixed']) or 'none'}; broken "
         f"{', '.join(d['broken']) or 'none'}.")
held_ids = {e.id for e in entries if e.status == "held"}
held_in_scoped = sum(bool(held_ids & set(v)) for v in loaded_scoped.values())
passed = {arm: sum(x["passed"] for x in r) for arm, r in runs.items()}
scoped = passed.get("scoped", -1)
learn.reveal(p_score, answer=0 if passed["whole file"] > scoped else 1
             if scoped > passed["whole file"] else 2,
             why="The store leaves out the four held entries and loads eight a question. "
             "What it leaves out cannot mislead, and what it fails to load cannot answer.")
(OUT / "runs.json").write_text(json.dumps({"runs": runs, "loaded": logs, "scale": scale},
                                          indent=2, default=str), encoding="utf-8")

d_s = diffs.get("scoped", {"fixed": [], "broken": []})
learn.record(
    k=K,
    store_entries=len(entries),
    held=len(held_ids),
    needed=len(needs),
    recall_recency=sum(arms["scope, recency"].values()),
    recall_bm25=sum(arms["scope, BM25"].values()),
    recall_embedding=sum(arms["scope, embeddings"].values()),
    recall_unscoped=sum(arms["no scope, BM25"].values()),
    leaked_unscoped=leaked,
    leaked_private=leaked_private,
    leaked_pellmar=leaked_pellmar,
    fiu_question_leaked=fiu_leaked,
    scale_entries=big["entries"],
    recall_bm25_1k=scale[1]["relevance"]["recall"],
    recall_bm25_10k=big["relevance"]["recall"],
    recall_embedding_1k=scale[1]["embedding"]["recall"],
    recall_embedding_10k=big["embedding"]["recall"],
    load_ms_bm25_10k=round(big["relevance"]["ms"]),
    load_ms_embedding_10k=round(big["embedding"]["ms"]),
    load_ms_bm25_base=round(scale[0]["relevance"]["ms"]),
    write_s_10k=round(big["write_s"], 1),
    embed_seconds=round(embed_seconds),
    whole_passed=passed["whole file"],
    scoped_passed=scoped,
    unscoped_passed=passed.get("unscoped", -1),
    scoped_fixed=len(d_s["fixed"]),
    scoped_broken=len(d_s["broken"]),
    held_loaded_scoped=held_in_scoped,
    mine=MINE is not None,
)

finding(f"""
The entry each memory question needs was among the {K} loaded on
{sum(arms['scope, recency'].values())} of 5 questions by recency,
{sum(arms['scope, BM25'].values())} by BM25 and {sum(arms['scope, embeddings'].values())} by
embeddings, all within the inquiry. Without scope, {leaked} of {26 * K} loaded entries came
from other inquiries, {leaked_private} of them other officers' private notes and
{leaked_pellmar} about another inquiry's Pellmar. At {big['entries']:,} entries BM25 found
{big['relevance']['recall']} of 5 in {big['relevance']['ms']:,.0f} ms a question, embeddings
{big['embedding']['recall']} of 5 in {big['embedding']['ms']:,.0f} ms. On the signed
questions: the whole file {passed['whole file']} of 26, the scoped store {scoped} of 26,
unscoped {passed.get('unscoped', -1)} of 26. Each session now starts with a chosen set of
memories, and the choice is recorded.
""")
save_shot("14-reading-from-memory")
