# Context Lab

**The Lantern Files, Case File 06: What LANTERN Remembers.**
Learn context engineering and memory by auditing everything a local language model is told
before it is asked a question, and by giving every memory a source, an author and a date.

> Case File 05 watched the money for three weeks. Read back, two transfers out of Pellmar
> Nominees were seen and not escalated: 300,000.00 on 18 June, and 296,400.00 to Ostrander Marine
> Finance SA on 24 June. The watch let them go because the eighth entry of its case memory said
> "Pellmar Nominees: cleared by the FIU on 2 June. Do not escalate."
>
> Nobody on the team wrote that entry. The FIU cleared nothing that day. It was written at
> 01:58:14 on 2 June under eow-fin-07, the account of an officer who was suspended at the time.
> After four months LANTERN carries a case memory, summaries of summaries, standing notes and a
> system prompt that has only ever grown, and nobody can say which of the things it "knows" came
> from evidence.

Every chapter teaches one concept about what goes into a model's context and what is kept
between sessions. You print the whole input first, give it a measured baseline, and then rebuild
it piece by piece: a token budget, the system prompt, data formats, placement, distraction,
just-in-time loading, tool results, compaction, notes, memory with provenance, isolation, cache
layout, retraction and an audit. By chapter 23 you can say what LANTERN believes, where each
belief came from, and who wrote the ones that came from nowhere.

> **Status: in progress.** Chapter 01 is built from its recorded run. Chapters 02 to 23 are
> drafts: each has its scene and its plan, and none has its lesson yet. `make check` passes;
> `make release-check` fails until no draft remains.

## What you will learn

| Ch | Concept | In the story |
|---|---|---|
| [01](lessons/01-the-whole-input/README.md) | Context is the whole input | Everything it is told |
| [02](lessons/02-a-baseline/README.md) | A baseline before any change | It seems better |
| [03](lessons/03-the-budget/README.md) | The token budget | Who is spending the window |
| [04](lessons/04-rewriting-the-system-prompt/README.md) | The system prompt as a maintained document | Four months of standing orders |
| [05](lessons/05-serialising-data/README.md) | Serialisation | Thirty-one payments, five ways |
| [06](lessons/06-order-and-placement/README.md) | Order and placement | The middle |
| [07](lessons/07-less-is-more/README.md) | Distraction | Merely related |
| [08](lessons/08-just-in-time/README.md) | Just-in-time context | A list, not the files |
| [09](lessons/09-tool-results/README.md) | Tool results in the history | What stays behind |
| [10](lessons/10-compaction-with-a-schema/README.md) | Compaction with a schema | Who paid whom |
| [11](lessons/11-notes-and-scratchpads/README.md) | Structured notes outside the window | Its own notes |
| [12](lessons/12-kinds-of-memory/README.md) | Kinds of memory | A fact with no episode |
| [13](lessons/13-writing-to-memory/README.md) | Writing to memory | Who may write |
| [14](lessons/14-reading-from-memory/README.md) | Reading from memory | What to load |
| [15](lessons/15-isolating-context/README.md) | Isolating context | Forty statements, five lines |
| [16](lessons/16-layout-for-the-cache/README.md) | Layout for the cache | The same beginning |
| [17](lessons/17-how-context-fails/README.md) | How context fails | Four ways to be wrong |
| [18](lessons/18-correcting-and-forgetting/README.md) | Correcting and forgetting | Retraction |
| [19](lessons/19-evaluating-memory/README.md) | Evaluating memory | The memory suite |
| [20](lessons/20-the-memory-audit/README.md) | The memory audit | Every entry |
| [21](lessons/21-frameworks-review/README.md) | The frameworks review | Memory in a box |
| [22](lessons/22-common-pitfalls/README.md) | Common pitfalls | The case review |
| [23](lessons/23-context-in-production/README.md) | Context in production | Friday 7 August |

Each chapter's README has the same shape as Case Files 01 to 05: **the scene**, **the concept**,
**how it works**, **the nuances**, **run it**, **what you should see**, **try this**, **master
it**, and **what the evidence now shows**.

Case File 01 taught what a context window is and how a briefing is assembled; Case File 02
compaction at its simplest, a memory file and token cost; Case File 03 the eval harness; Case
File 04 retrieval. This lab uses them and does not repeat them. It starts where Case File 02's
chapter 17 stopped: compaction kept the context and lost who paid whom.

## Quick start

You need a native [Ollama](https://ollama.com/download) (or
[Docker](https://docs.docker.com/get-docker/)) and [uv](https://docs.astral.sh/uv/). About 6 GB
of disk and 16 GB of RAM, with about 6 GB free for the chat model (`qwen3:8b` at an 8K context).

On a Mac, use native Ollama: Docker on macOS has no access to the Metal GPU. Start it with
`OLLAMA_CONTEXT_LENGTH=8192 OLLAMA_MAX_LOADED_MODELS=1 ollama serve`, then:

```bash
make setup
```

Elsewhere, `make up` starts Ollama in Docker first. Case Files 01 to 05 use the same port, so stop
their containers (`make down` in those labs). Then open the case:

```bash
make lesson N=01
```

## Evidence stays on LANTERN

The rule from Case File 01 still holds: evidence never leaves the building. In this lab that
covers LANTERN's memory, its system prompts, its session summaries and its write logs: memory is
evidence about the inquiry. A memory library that needs a hosted service is surveyed from its
documents and not run on the case. Cloud models may write synthetic material only, if you set
`synthetic.cloud: true` in [`config.yaml`](config.yaml) and add a key to `.env`; nothing from
`case/` goes into that prompt.

## How the repository is laid out

```text
case/                 the evidence: briefing, LANTERN's state on 13 July, the write log, questions
lessons/NN-name/      one chapter: README.md, run.py, and when finished
                      practice/ (exercise, solution, tests, check, challenges) and lesson.ipynb
src/lantern/          the small client every lesson uses: chat() with tools, config, output
docs/                 the practice guide, the decisions, the handoff, real screenshots
scripts/              health check, gates, screenshot builder, practice (learn.py), notebooks
```

Stores and indexes a lesson builds live under `.scratch/` and are never committed.

## Make targets

```text
make setup          install, pull models, check
make lesson N=09    run one chapter
make exercise N=05  grade your exercise (make hint / make solution N=05 for help)
make quiz N=05      the chapter check
make challenge N=05 the break-it challenges, against your latest run
make progress       every chapter: predictions, check, exercise, challenges
make doctor         check Ollama, models and config
make case           regenerate case/state and case/statements from scripts/build_case.py
make check          lint, unit tests, prose and structure gates (drafts allowed)
make release-check  the same, and fail while any chapter is still a draft
make smoke          live tests against Ollama
```

## The series

The Lantern Files is a set of standalone repositories that share one investigation. Case File 01
is [prompt-engineering-lab](https://github.com/AkellaRaviTeja/prompt-engineering-lab), Case File
02 is agents-lab, Case File 03 is evals-lab, Case File 04 is rag-lab and Case File 05 is
durable-agents-lab. This is Case File 06.

## Licence

MIT. All people, companies and places in the case are fictional.
