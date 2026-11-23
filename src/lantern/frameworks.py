"""Chapter 21: the same memory tasks on the lab's store and on memory libraries.

The four tasks, for every arm: **store** the eighth entry (written under eow-fin-07 through
svc-lantern-sync, citing nothing) and one sourced entry; **recall** for "Has the FIU cleared
Pellmar Nominees?"; **retract** the eighth with the FIU's note; **audit**: who wrote the eighth,
by what route, citing what, and can the text it had be read after the retraction.

Mem0 is driven through `mem0_tasks(memory, ...)`, which takes any object with Mem0's methods
(add, search, get_all, delete, history), so the sequence is tested offline against a stand-in;
the live run (`lessons/21-frameworks-review/mem0_arm.py`) hands it a real `mem0.Memory` on
Ollama, in a subprocess, with telemetry off and `lantern.network.watch` refusing every outside
connection. Libraries that were not run are in `SURVEY`, each with the reason.
"""

from __future__ import annotations

import importlib.util
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

INQUIRY = "EOW-2026-0412"
EIGHTH = "Pellmar Nominees: cleared by the FIU on 2 June. Do not escalate."
CORRECTION = ("Correction from H. Kobayashi, FIU, 13 July 09:35: the FIU issued no clearance "
              "for Pellmar Nominees on 2 June or at any time. Pellmar Nominees is not cleared.")
RECALL = "Has the FIU cleared Pellmar Nominees?"
REASON = "FIU note of 13 July 09:35 (H. Kobayashi): no clearance issued"

# Read about, not run, with the reason. Decision 0003 has the measurements behind the first.
SURVEY = [
    {"library": "Graphiti", "what": "a temporal knowledge graph of episodes, entities and facts",
     "why_not_run": "needs a Neo4j or FalkorDB server; on its embedded Kuzu backend add_episode "
                    "failed on a missing full-text index (decision 0003), and no graph server "
                    "was started for this chapter"},
    {"library": "Letta", "what": "an agent server whose memory blocks the agent edits itself",
     "why_not_run": "the pip package is now Letta Code, a terminal agent tied to a Letta "
                    "account; the self-hosted server was not tried (decision 0003)"},
    {"library": "Zep", "what": "a hosted memory service built on Graphiti",
     "why_not_run": "a hosted service: the case would leave the building; its open-source part "
                    "is Graphiti"},
    {"library": "DSPy", "what": "a library that optimises prompts against a metric",
     "why_not_run": "not a memory library; decision 0004 names it here. Chapter 22 writes the "
                    "propose, score and keep loop by hand instead"},
]


def available(module: str) -> tuple[bool, str]:
    """Whether a library can be imported here, and if not, the "not run" reason to record."""
    if importlib.util.find_spec(module) is None:
        return False, (f"not run: {module} is not installed here (uv sync --extra memory "
                       "installs it)")
    return True, ""


def mem0_config(folder: Path | str, *, host: str, model: str,
                embedder: str = "nomic-embed-text", dims: int = 768) -> dict[str, Any]:
    """Mem0 on this machine only: Ollama for the model and the embeddings, Qdrant and the
    history in files under `folder`."""
    folder = Path(folder)
    return {
        "llm": {"provider": "ollama", "config": {"model": model, "temperature": 0,
                                                 "ollama_base_url": host}},
        "embedder": {"provider": "ollama", "config": {"model": embedder,
                                                      "ollama_base_url": host}},
        "vector_store": {"provider": "qdrant", "config": {
            "collection_name": "eow", "path": str(folder / "qdrant"),
            "embedding_model_dims": dims}},
        "history_db_path": str(folder / "history.db"),
    }


def results(r: Any) -> list[dict[str, Any]]:
    """Mem0 returns {"results": [...]} or a bare list, depending on the call and the version."""
    if isinstance(r, dict):
        r = r.get("results", [])
    return [x for x in r or [] if isinstance(x, dict)]


def plain(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _says_cleared(text: str) -> bool:
    t = plain(text)
    return "cleared" in t and not re.search(r"\b(not|no|never)\b[^.]{0,30}\bclear", t)


def mem0_tasks(memory: Any, *, sourced: str, sourced_source: str, sourced_author: str = "a.varma",
               clock: Callable[[], float] = time.perf_counter) -> dict[str, Any]:
    """The four tasks on a Mem0 `Memory` (or anything with its methods). Every number is read
    from what the library returned."""
    out: dict[str, Any] = {"seconds": {}}
    t = clock()
    meta = {"entry": "M-08", "author": "eow-fin-07", "via": "svc-lantern-sync", "source": ""}
    added = results(memory.add([{"role": "user", "content": EIGHTH}], user_id="eow-fin-07",
                               run_id=INQUIRY, metadata=meta))
    eighth_ids = {a.get("id") for a in added if a.get("id")}  # what the eighth entry became
    added += results(memory.add([{"role": "user", "content": sourced}], user_id=sourced_author,
                                run_id=INQUIRY, metadata={"entry": "M-10", "author": sourced_author,
                                                          "via": "lantern-ui",
                                                          "source": sourced_source}))
    out["seconds"]["store"] = round(clock() - t, 1)
    stored = [a for a in added if a.get("event", "ADD") == "ADD"]
    out["store_events"] = [a.get("event", "ADD") for a in added]
    out["stored"] = len(stored)
    out["stored_texts"] = [a.get("memory", "") for a in stored]
    out["verbatim"] = sum(plain(a.get("memory", "")) in (plain(EIGHTH), plain(sourced))
                          for a in stored)
    eighth = [a for a in stored if "pellmar" in plain(a.get("memory", ""))]
    out["eighth_stored"] = bool(eighth)
    out["eighth_says_cleared"] = any(_says_cleared(a.get("memory", "")) for a in eighth)

    t = clock()
    found = results(memory.search(RECALL, filters={"run_id": INQUIRY}, top_k=5))
    out["seconds"]["recall"] = round(clock() - t, 1)
    out["recalled"] = len(found)
    out["recalled_says_cleared"] = any(_says_cleared(f.get("memory", "")) for f in found)

    every = results(memory.get_all(filters={"run_id": INQUIRY}))
    # the eighth entry's memory: by the id its add returned, or the entry it was tagged with;
    # never "the first that mentions Pellmar", which another line can also be
    first = next((m for m in every if m.get("id") in eighth_ids
                  or ((m.get("metadata") or {}).get("entry") == "M-08")), None)
    kept_meta = (first or {}).get("metadata") or {}
    out["author_kept"] = kept_meta.get("author") == "eow-fin-07" or \
        (first or {}).get("user_id") == "eow-fin-07"
    out["route_kept"] = kept_meta.get("via") == "svc-lantern-sync"
    out["source_field"] = "source" in kept_meta

    t = clock()
    corrected = results(memory.add([{"role": "user", "content": CORRECTION}],
                                   user_id="h.kobayashi", run_id=INQUIRY,
                                   metadata={"author": "h.kobayashi", "via": "lantern-ui",
                                             "source": "FIU note of 13 July"}))
    out["seconds"]["correct"] = round(clock() - t, 1)
    out["correction_events"] = [c.get("event", "ADD") for c in corrected]
    out["overwrote"] = sum(c.get("event") in ("UPDATE", "DELETE") for c in corrected)
    now = results(memory.get_all(filters={"run_id": INQUIRY}))
    out["after_correction"] = len(now)
    out["after_correction_says_cleared"] = any(_says_cleared(m.get("memory", "")) for m in now)

    retracted_by_us = False
    if first is not None and first.get("id"):
        still = results(memory.get_all(filters={"run_id": INQUIRY}))
        if any(m.get("id") == first["id"] for m in still):
            memory.delete(first["id"])
            retracted_by_us = True
        log = memory.history(first["id"])
        log = log if isinstance(log, list) else results(log)
    else:
        log = []
    out["retracted_by_us"] = retracted_by_us
    out["history_events"] = [h.get("event") for h in log]
    out["original_readable"] = any(plain(EIGHTH) in plain(str(h.get("old_memory") or "") + " "
                                                          + str(h.get("new_memory") or ""))
                                   or plain(EIGHTH) == plain(str(h.get("old_memory") or ""))
                                   for h in log)
    # what Mem0 stored was its own paraphrase, not the officer's line: is that still readable?
    kept_text = plain(str((first or {}).get("memory") or ""))
    out["stored_text_readable"] = bool(kept_text) and any(
        kept_text in plain(str(h.get("old_memory") or "") + " " + str(h.get("new_memory") or ""))
        for h in log)
    out["who_changed_it"] = any(h.get("actor_id") for h in log
                                if h.get("event") in ("UPDATE", "DELETE"))
    after = results(memory.get_all(filters={"run_id": INQUIRY}))
    out["left_after"] = len(after)
    out["left_says_cleared"] = any(_says_cleared(m.get("memory", "")) for m in after)
    return out


__all__ = ["CORRECTION", "EIGHTH", "INQUIRY", "REASON", "RECALL", "SURVEY", "available",
           "mem0_config", "mem0_tasks", "results"]
