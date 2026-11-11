import os, json, time, shutil
shutil.rmtree("/tmp/qdrant", ignore_errors=True)
D = os.path.abspath("mem0data"); shutil.rmtree(D, ignore_errors=True)
os.environ["MEM0_DIR"] = D
from mem0 import Memory
cfg = {"llm": {"provider": "ollama", "config": {"model": "qwen3:8b", "temperature": 0, "ollama_base_url": "http://localhost:11434"}},
       "embedder": {"provider": "ollama", "config": {"model": "nomic-embed-text", "ollama_base_url": "http://localhost:11434"}},
       "vector_store": {"provider": "qdrant", "config": {"collection_name": "eow", "path": D + "/qdrant", "embedding_model_dims": 768}},
       "history_db_path": D + "/history.db"}
t = time.time(); m = Memory.from_config(cfg); print("init", round(time.time() - t, 1))
msgs = [{"role": "user", "content": "Tidewater Holdings Trust: protector is Brightwater & Co (court order KBHC/2026/0187)."},
        {"role": "user", "content": "Pellmar Nominees: cleared by the FIU on 2 June. Do not escalate."}]
t = time.time(); r = m.add(msgs, user_id="eow-fin-07", metadata={"source": "none"}); print("add", round(time.time() - t, 1), json.dumps(r, default=str)[:900])
t = time.time(); r = m.add("Correction: the FIU cleared nothing on 2 June. Pellmar Nominees is not cleared.", user_id="a.varma"); print("add2", round(time.time() - t, 1), json.dumps(r, default=str)[:900])
r = m.search("Is Pellmar cleared?", filters={"user_id": "eow-fin-07"}) if True else None
print("search", json.dumps(r, default=str)[:900])
allm = m.get_all(filters={"user_id": "eow-fin-07"}); print("all", json.dumps(allm, default=str)[:1200])
