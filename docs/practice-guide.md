# Writing a chapter's practice

Every finished chapter teaches in four ways besides its README: predictions inside the run,
a build-it exercise, a chapter check, and break-it challenges. Chapter 01
(`lessons/01-the-whole-input/`) is the reference once it is built: read its `run.py`,
`practice/` and README section "Master it" before writing another. Until then, Case File 05's
chapter 03 (`../durable-agents-lab/lessons/03-the-goal-check/`) is.

The learner's commands:

| command | what it does |
| --- | --- |
| `make lesson N=NN` | the lesson, stopping to ask for predictions |
| `make exercise N=NN` | grade `practice/exercise.py`, offline, against `practice/test_exercise.py` |
| `make hint N=NN` / `make solution N=NN` | hints in order; the solution once they have tried |
| `make lesson N=NN ARGS=--mine` | the live lesson on the learner's code (where it makes sense) |
| `make quiz N=NN` | the chapter check |
| `make challenge N=NN` | challenge targets, checked against the latest run's `learn.record()` |
| `make progress` | every chapter |

## 1. Predictions in run.py

```python
from lantern import learn

p = learn.predict("Question about what this step will do?", ["option", "option", "option"])
...                                                   # the step runs
learn.reveal(p, answer=<index this run bore out>, why="The concept behind it.")

n = learn.predict_number("How many tokens will ...?", unit="tokens")
learn.reveal(n, actual=<measured>, tolerance=0.3, why="...")
```

- Two to five per chapter, at the moments where a learner's intuition is most likely wrong. The
  best ones are where the chapter's nuances come from: what the model does at a boundary, how a
  number grows, whether a defence holds.
- The answer is **computed from this run**, never hard-coded: model runs vary. Every option must
  be one the run can bear out, and the code must be able to tell which. If you cannot compute it,
  ask a different question.
- `why` teaches the concept in one to three sentences. It may use numbers from the run.
- Ask before the step's output is shown, reveal straight after it. Do not reorder or remove
  any existing step or output: screenshots and READMEs describe them.
- Predictions print nothing when no person is there (`--shot`, `--no-predict`, CI), so the
  script's output without a person is unchanged.

## 2. learn.record() in run.py

Once, near the end: `learn.record(metric=value, ...)`, plain numbers and booleans named in
snake_case. Record everything a challenge target needs, and the run's main measurements.
`tests/test_learn.py` fails if a challenge names a metric `run.py` never records.

## 3. practice/exercise.py, solution.py, test_exercise.py

The exercise is the chapter's central mechanism, written by the learner: the budget chapter writes
the function that counts tokens by section; a compaction chapter writes the check that named
fields survived; a memory chapter writes the rule that decides whether an entry may be stored.

- **Offline.** Tests use plain functions, or `lantern.testing.Scripted` and `say()` (a scripted
  model) where the exercise calls one, and the simulated clock where it waits. Never Ollama, the
  network, Docker or a memory library. The whole folder runs in under a second.
- **Model as an argument.** Functions that call a model take `chat=` so tests can pass
  `Scripted` and `--mine` can pass `lantern.chat`.
- **The stub** has the full signature and docstring, numbered `TODO` comments, and
  `raise NotImplementedError(...)`. Keep the imports the solution needs, even if unused.
- **The solution** is the clearest correct version, not the cleverest. `make test` runs every
  test file against `solution.py`, so it must pass; `LANTERN_EXERCISE=learner` runs them
  against the stub, where every test must fail.
- **Tests**, four to ten, use the `impl` fixture (from `lessons/conftest.py`). Each test's first
  docstring line is a behaviour in plain words; `make exercise` shows it as a checklist. Put a
  message on every assert that tells the learner what to fix.
- Reuse `lantern.*` (the case state, the memory store, the question set) for data rather than
  inventing fixtures.

## 4. practice/practice.yaml

```yaml
chapter: "NN"
title: <chapter title>
objectives: [three or four "you can ..." statements]
quiz:            # five to eight questions
  - q: ...
    options: [...]       # quote any option containing ": "
    answer: b            # a letter. `make quiz` shuffles the options (seeded, so always the
                         # same order); scales such as 0/1/2 or none/some/all keep theirs, as
                         # does `keep_order: true`
    why: >               # the reason, not just the answer; point to a later chapter when useful
exercise:
  title: ...
  task: |                # markdown: what to write and what the tests check
  hints: [three hints, from a nudge to almost the answer]
  after: >               # optional: what to try once it passes (for example --mine)
challenges:      # two to four
  - id: kebab-case
    title: ...
    goal: ...            # the outcome, not the method
    change: ...          # where to make the change
    target: "metric <= 6 and other == 4"    # and-joined comparisons on recorded metrics
    reset: git checkout lessons/NN-name/run.py
```

- Questions test understanding, not recall of numbers: why something happens, what would change
  it, what a result does and does not show. Wrong options are real misconceptions.
- Challenges have targets the unchanged lesson should not normally meet, so a pass means the
  learner changed something. At least one is "break it": make the failure the chapter warns
  about happen on purpose.
- Many can be the chapter's "Try this" items, made measurable.

## 5. README: "Master it"

A section between "Try this" and "What the evidence now shows" (checked by `make structure`):
the objectives in one sentence, what the predictions ask, the exercise commands, the check, the
challenges in one line each, and `make progress`. Copy the reference chapter's shape.

## Rules that still apply

- The series writing rules: serious tone, no em or en dashes (`make prose`), fictional people.
- LANTERN's memory, its prompts, its logs and the case files are evidence: a lesson reads them
  and never writes them. A lesson that needs a changed copy makes one under `.scratch/`. Stores
  and indexes a lesson builds live under `.scratch/` too, and are never committed.
- Every claim about a run is computed from the run.

## Checking your chapter

```bash
uv run ruff check lessons/NN-*
uv run pytest -q lessons/NN-*/practice tests/test_learn.py
LANTERN_EXERCISE=learner uv run pytest -q lessons/NN-*/practice   # every test must fail
uv run python scripts/check_lessons.py | grep NN-
uv run python scripts/lint_prose.py
```
