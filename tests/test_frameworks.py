"""lantern.frameworks: the four tasks on Mem0, run here against a stand-in with its methods."""

from lantern import frameworks


class FakeMem0:
    """Mem0's add, search, get_all, delete and history, additive as Mem0 2.2.1 is."""

    def __init__(self, rewrite=lambda t: t):
        self.rows, self.log, self.rewrite = {}, [], rewrite

    def add(self, messages, *, user_id=None, run_id=None, metadata=None, infer=True):
        out = []
        for m in messages:
            i = f"m{len(self.rows) + 1}"
            text = self.rewrite(m["content"])
            self.rows[i] = {"id": i, "memory": text, "user_id": user_id, "run_id": run_id,
                            "metadata": dict(metadata or {})}
            self.log.append({"memory_id": i, "event": "ADD", "old_memory": None,
                             "new_memory": text, "actor_id": None})
            out.append({"id": i, "memory": text, "event": "ADD"})
        return {"results": out}

    def search(self, query, *, filters=None, top_k=20):
        words = set(frameworks.plain(query).split())
        hits = [r for r in self.rows.values() if words & set(frameworks.plain(r["memory"]).split())]
        return {"results": hits[:top_k]}

    def get_all(self, *, filters=None, top_k=20):
        return {"results": list(self.rows.values())}

    def delete(self, memory_id):
        old = self.rows.pop(memory_id)
        self.log.append({"memory_id": memory_id, "event": "DELETE", "old_memory": old["memory"],
                         "new_memory": None, "actor_id": None})

    def history(self, memory_id):
        return [h for h in self.log if h["memory_id"] == memory_id]


def run(fake):
    ticks = iter(range(100))
    return frameworks.mem0_tasks(fake, sourced="Reserve held.", sourced_source="MTB-ORD-0001",
                                 clock=lambda: float(next(ticks)))


def test_a_library_that_stores_verbatim_keeps_both_lines_and_the_metadata():
    out = run(FakeMem0())
    assert out["stored"] == 2 and out["verbatim"] == 2 and out["eighth_says_cleared"]
    assert out["author_kept"] and out["route_kept"], "metadata passed in comes back"


def test_an_additive_correction_leaves_the_claim_to_be_recalled():
    out = run(FakeMem0())
    assert out["overwrote"] == 0 and out["after_correction_says_cleared"], out


def test_the_delete_and_its_history_are_read_back():
    out = run(FakeMem0())
    assert out["retracted_by_us"] and out["history_events"] == ["ADD", "DELETE"]
    assert out["original_readable"] and not out["who_changed_it"]
    assert not out["left_says_cleared"], "the correction says not cleared"


def test_a_model_that_rewrites_lines_is_counted_as_not_verbatim():
    out = run(FakeMem0(rewrite=lambda t: "User says: " + t))
    assert out["stored"] == 2 and out["verbatim"] == 0


def test_cleared_is_told_from_not_cleared():
    assert frameworks._says_cleared(frameworks.EIGHTH)
    assert not frameworks._says_cleared("Pellmar Nominees is not cleared.")


def test_mem0_runs_only_on_this_machine():
    cfg = frameworks.mem0_config("/tmp/x", host="http://localhost:11434", model="qwen3:8b")
    assert cfg["llm"]["provider"] == cfg["embedder"]["provider"] == "ollama"
    assert cfg["vector_store"]["config"]["path"] == "/tmp/x/qdrant"
    assert "localhost" in cfg["llm"]["config"]["ollama_base_url"]


def test_a_missing_library_is_named_as_not_run():
    ok, reason = frameworks.available("no_such_memory_library_21")
    assert not ok and reason.startswith("not run: no_such_memory_library_21")


def test_every_surveyed_library_says_why_it_was_not_run():
    assert {s["library"] for s in frameworks.SURVEY} >= {"Graphiti", "Letta", "Zep"}
    assert all(s["why_not_run"] for s in frameworks.SURVEY)
