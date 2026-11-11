# Decisions

The plan for Case File 06 left three decisions open. Each was settled on 11 November 2026, two
of them from measurements on this machine (the Mac, 16 GB, native Ollama 0.40.15, qwen3:8b).
The scripts and their raw output are in [`spikes/`](spikes/); run them from the repository root
with `uv run python docs/decisions/spikes/<name>.py <output.json>` (they read `../agents-lab`).

| # | Decision | Choice | Decided by | Record |
|---|---|---|---|---|
| 1 | TOON: its own chapter, or one row in a table of formats | One row in chapter 05 | The author | [0001](0001-toon-is-one-row-in-chapter-05.md) |
| 2 | How to show cache savings on Ollama | Prompt evaluation seconds, with the unchanged token count beside them | Proposed, awaiting the author | [0002](0002-cache-savings-are-shown-in-seconds.md) |
| 3 | Whether the memory libraries run offline, and so what chapter 21 is | Run Mem0, try Graphiti on Neo4j, survey Letta and Zep | The author | [0003](0003-chapter-21-runs-mem0-and-tries-graphiti.md) |
