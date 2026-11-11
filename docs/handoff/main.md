# main: context-lab, Case File 06 (What LANTERN Remembers), scaffold
Updated: 2026-11-11   Branch: main, scaffold commit only. No GitHub repository yet.
Gate: make check passes: ruff clean, 22 passed and 4 skipped (no finished chapter has practice
yet), prose 0 problems, structure 23 lessons 23 drafts. `make notebooks-check` fails with 0
notebooks, as a gate on empty input should.
Machine: the Mac (16 GB, Apple silicon), native Ollama 0.40.15 with qwen3:8b.

## Next (do this first)
- The three open decisions of the plan, measured and recorded in `docs/decisions/`.
- `scripts/build_case.py`: LANTERN's state on 13 July from one seed (standing orders and their
  versions, the case memory with its eight entries, session summaries, standing notes, tool
  descriptions, the write log), with `tests/test_case_facts.py` pinning what it must keep from
  Case Files 02 to 05.
- Chapter 01, "Everything it is told" (`lessons/01-the-whole-input/`). It is the reference
  chapter for practice; build it first, with its `practice/` folder.

## What the scaffold carries over from durable-agents-lab (Case File 05, scaffold a2516cf)
- `src/lantern`: `config`, `llm` (chat, stream, tools, OpenRouter), `cloud`, `case`, `learn`,
  `ui`, `testing`. Not carried: the watch, the journal, the bank feed, the gate.
- `scripts`: `doctor`, `check_lessons`, `lint_prose`, `learn`, `build_notebooks`, `svg_to_png`.
  Tests: gates, client, learn, stream.
- Makefile: only targets with a script here. Not carried: `case` (added with
  `scripts/build_case.py`), the engines extra.

## Not done
- No GitHub repository (the user creates it). Nothing pushed.
- Every scene and planned beat is a proposal from the roadmap; rewrite each from its run.
