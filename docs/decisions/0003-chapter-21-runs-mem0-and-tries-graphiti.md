# 0003: Chapter 21 runs Mem0 and tries Graphiti

Status: Accepted, 11 November 2026 (the author chose the recommended option).

## Context

Chapter 21 reviews memory libraries against the lab's own store. Memory is evidence, so a
library is run on the case only if it runs with no connection leaving the machine. The plan
said that if none can, the chapter is a survey.

Measured on 11 November 2026 with `spikes/mem0_spike.py` and `spikes/graphiti_spike.py`, each
run behind `spikes/proxy.py`, a local proxy that refuses every outside connection and logs what
was asked for (Ollama on localhost is exempt).

| Library | Ran offline | What the proxy saw | Notes |
|---|---|---|---|
| Mem0 2.2.1 | Yes, on Ollama (qwen3:8b, nomic-embed-text) and a Qdrant file | 24 attempts to `us.i.posthog.com` and 1 to `raw.githubusercontent.com` by default; none with `MEM0_TELEMETRY=False` | Its first `add`, two plain facts including the Pellmar entry, took 65 s and stored nothing. A correction stored two memories in 21 s. `get_all` and `search` for the first author returned nothing |
| Graphiti 0.31.2 | No, on the embedded Kuzu backend | 12 attempts to `us.i.posthog.com` by default; none with `GRAPHITI_TELEMETRY_ENABLED=false` | `add_episode` fails on a missing full-text index; the Kuzu backend is marked deprecated. Neo4j or FalkorDB in Docker was not tried |
| Letta | Not run | | `pip install letta` (0.34.12) is now Letta Code, a terminal agent tied to a Letta account. The self-hosted server was not tried |
| Zep | Not run | | A hosted service; its open-source part is Graphiti |

## Options

1. Run the lab's own store and Mem0; try Graphiti on Neo4j in Docker when the chapter is built,
   and survey it if it does not run; survey Letta and Zep from their documents.
2. Run Mem0 only and survey the rest.
3. Survey only.

## Decision

Option 1.

## Consequences

- Chapter 21 gets an optional extra (`memory`: mem0ai, qdrant-client, graphiti-core) and, if
  Graphiti runs, a Neo4j service under a Compose profile. No other chapter needs either.
- Telemetry is off in the lab's configuration for both libraries, and the chapter shows the
  count of attempts with it left on, behind the same refusing proxy.
- The chapter states for each library whether it was run or read about.
- Mem0 needs an embedding model. `nomic-embed-text` is added to `config.yaml` by the first
  chapter that needs one.
- Would change the decision: Graphiti failing on Neo4j as well (then it is surveyed), or Mem0
  making an outside call with telemetry off (then it is not run on the case).
