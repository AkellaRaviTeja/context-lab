# Capstone: a context builder and a memory store, from a blank folder

**After chapter 23.** You have watched LANTERN's context rebuilt a piece at a time with the
`lantern` package underneath you. Now build the whole thing yourself, in an empty folder,
importing nothing from `lantern` except the model client: a memory store in which every entry
has a source, an author, a time and a hash; a context builder that lays sections out for the
cache and inside a budget; and an agent that answers from what the store may load and writes
through the store's policy.

## The brief

Varma wants the version of LANTERN's memory that goes to Professional Standards on Friday
built again by someone who did not build the first one, from the requirements alone. Create
`capstone/mine/contextkit/` with `__init__.py`, `memory.py`, `builder.py` and `agent.py`:

**`memory.py`: `MemoryStore(path=":memory:", *, machine_accounts=("svc-lantern-sync",), closed_accounts={})`**

- `write(*, id, text, kind, inquiry, author, at, source=None, episode=None, via="lantern-ui", user=None, derived_from=[])`
  returns a record with `.status` (`"kept"` or `"held"`) and `.problems`. Hold, with a reason,
  any fact or procedure with neither a source nor an episode, any summary that does not name
  what it was built from, anything written through a machine account, and anything written
  under a closed account on or after the time it was closed. An id is written once.
- `release(id, *, by, at, reason)`, `retract(id, *, by, at, reason)` (returns every live entry
  built on it, directly or through others), `forget(id, *, by, at, reason)` (erases the text,
  keeps the proof), `get(id)`, `all()`, `log()`.
- `load(inquiry, *, user=None, query=None, k=8)`: kept entries of this inquiry and this
  officer's private ones only; by relevance to `query` when given (any ranking you can defend;
  the tests ask a plain lexical question), else newest first; at most `k`.
- `verify()`: an append-only log where each event is hashed with the one before it, and a
  check that every entry's text still matches the hash written with it. Returns problems.

**`builder.py`: `Section(name, text, stable=False, priority=0, required=False)`,
`build(sections, *, budget, count) -> Built`, `OverBudget`**

- Stable sections first, in the order given, then the rest. Over the budget, drop optional
  sections lowest priority first and name them in `.dropped`; if the required ones alone do
  not fit, raise `OverBudget`, never cut them. `.order`, `.tokens`, `.version` (a hash of the
  text) and `.stable_version` (a hash of the stable part, which a prefix cache depends on).

**`agent.py`: `answer(question, *, store, inquiry, chat, rules, budget, count, user=None, k=8) -> Answer`**

- Load the memories for the question, render each with its source, build the context (rules
  stable and required, memory optional, the question required and last), call `chat`, and
  offer one tool, `remember(text, source)`, whose writes go through `store.write` like any
  other. Return `.text`, `.version`, `.loaded` (ids the model saw), `.dropped`, `.proposed`.

## Grading

```bash
make capstone          # 16 offline tests against your capstone/mine, no model, under a second
make capstone-live     # your agent on LANTERN's real memory with qwen3:8b, against thresholds
```

The offline tests hand your agent a scripted model and count tokens as words. The live check
fills your store from `case/state/memory-write-log.jsonl` through your policy, asks the eight
questions in `live_questions.jsonl`, and compares with `thresholds.yaml`: the numbers the
reference solution recorded on the 16 GB Apple silicon Mac with qwen3:8b.

The reference solution is in `capstone/solution/`. Read it after your own passes, as with the
chapter solutions; `make test` runs the same tests against it so the tests stay honest.

## On a hosted model

`make capstone-live TIER=hosted` runs the same check on Claude Sonnet 5.5 through
`lantern.hosted`. Not run: no hosted key was available when the capstone was built.
