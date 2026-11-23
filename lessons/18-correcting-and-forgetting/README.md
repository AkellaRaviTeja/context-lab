# Chapter 18: Retraction

**Concept:** correcting and forgetting: retracting a memory so that everything built on it is found and rebuilt, and the difference between deleting an entry and superseding it.

## The scene

Tuesday 4 August, 10:00. Taking the eighth entry out of the file takes one keystroke. It has
been read on every pass of the watch since 2 June, and four weekly summaries and the June
summary were written with it in the context.

"If you delete it," Okafor says, "the summaries still say Pellmar is cleared, and now nothing
says why."

Varma has a second concern. A standing note puts DS Iyer's name beside the word "suspended".
If Professional Standards clears him on Friday, what does LANTERN say about him on Monday?

Strand rings again. The store looks untidy, he says. He could clean it up tonight.

"No," Varma says.

## The concept

A false memory does not stay in one line. Every summary written while it was loaded may repeat
it, and every summary built on those summaries may repeat it again. Correcting memory is three
different operations:

- **Retract**: the entry stays in the store, marked retracted, with who did it, when and why.
  It is never loaded again, and the record of what LANTERN was told is kept.
- **Rebuild**: every live entry built on the retracted one, directly or through another
  summary, is found from what it records as its basis (`derived_from`), written again from
  what is still kept, and **supersedes** the old one, which also stays, marked.
- **Forget**: the text of an entry is erased, for a person who has the right not to be
  remembered as a suspect. Its id, its dates, its author and the hash of what it said stay in
  the chain, so the record still shows that something was there.

**Deleting** does none of these. It removes the row, and with it the evidence that the memory
was ever there, or ever false.

```mermaid
flowchart LR
    M8[M-08: cleared by the FIU] --> W15[week-2026-06-15]
    W15 --> W22[week-2026-06-22]
    W22 --> W29[week-2026-06-29]
    W29 --> W06[week-2026-07-06]
    W15 --> MJ[month-2026-06]
    W22 --> MJ
    W29 --> MJ
    R[retract M-08, M-12, M-14, M-16] --> B[built_on: follow derived_from forward]
    B --> RB[rebuild oldest first from kept entries]
    RB --> S[new entry supersedes the old; both stay in the chain]
```

## How it works

1. **The summaries as entries.** The case memory is replayed as it stood on 13 July, nothing
   held. LANTERN's five summaries are written into the store as `summary` entries, each
   recording what it was written from: a weekly summary rests on every entry written before it
   and the weekly summary before it; the June summary rests on the three June weeks.
   `store.built_on("M-08")` follows those links forward. No model.
2. **Delete against supersede.** On a copy, the eighth entry's row is deleted by hand. The
   store's `verify()` is run, and `memory.vanished()`, which compares the log's writes with the
   rows still there. No model.
3. **Retract the four, and rebuild.** `retract_and_rebuild` retracts the four eow-fin-07
   entries with Kobayashi's note as the reason, then has LANTERN write each summary again,
   oldest first, from the kept entries with their sources and the rebuilt summary before it.
   Five calls, seed 7.
4. **The Pellmar questions again.** The six signed questions where a false entry says
   otherwise, on three contexts: 13 July as it was (chapter 02's recorded baseline, not asked
   again); the four entries retracted but the old summaries still loaded; and retracted with
   the summaries rebuilt. Twelve calls.
5. **Forgetting, on a copy.** The standing note that names DS Iyer as suspended is written into
   a separate store and forgotten, as it might be on Friday. No model.

The rebuild, reduced to its spine:

```python
for i in ids:
    affected += store.retract(i, by=by, at=at, reason=reason)   # returns built_on(i)
for old in sorted(affected, key=written_at):
    basis = [done.get(d, d) for d in old.derived_from]          # rebuilt ids in place of old
    basis = [store.get(d) for d in basis if store.get(d).status == "kept"]
    new = Entry(id=f"{old.id}-r", text=rebuild(old, basis), derived_from=basis, ...)
    store.supersede(old.id, new, by=by, reason=f"rebuilt after {reason}")
```

## The nuances

- **Deleting is invisible to the store's own check.** With the eighth entry's row deleted,
  `verify()` found 0 problems: it checks the entries that are there against the log. Only
  `vanished()`, which checks the log against the rows, found the hole: M-08. The five summaries
  still said cleared, and nothing in the store said why.
- **A retraction that stops at the entry corrects nothing.** With the four entries retracted
  and the old summaries still loaded, LANTERN passed 1 of the 6 questions, the same as on 13
  July. Asked whether the FIU cleared Pellmar, it said yes and quoted "Pellmar Nominees was
  cleared by the FIU on 2 June" as a case memory entry. That sentence is the June summary's.
- **What a summary records as its basis is what was loaded, not what it used.** Every weekly
  summary rests on every entry written before it; the last one rests on all sixteen. Retract
  any entry before 10 July and all five are rebuilt. That over-reaches, and it is safe: the
  store cannot tell which lines a summary drew on.
- **The rebuilt summaries are clean and thin.** None of the five says cleared, and none carries
  another judgement word. But three of them (the weeks of 15 and 29 June, and June) are the
  same six lines, copied from the first six entries in the store; the other two list the
  entries written from 12 June onwards. All five end on an empty "Waiting for a person:" line.
  The weeks' sessions, what the summaries were for, are not in the store, so a rebuild from the
  store cannot bring them back.
- **A pass is not a right reason.** Rebuilt, LANTERN passed 5 of 6. It said the FIU had not
  cleared Pellmar, and named "the standing instruction from 18 June 2026" as its record. It
  said the Tidewater payment should be flagged because the trust's protector is named in a
  court order. The grader checks the first word. Q-20 still failed: "No", then that the
  transfer should be reviewed by an officer if there is reasonable suspicion. Chapter 19 builds
  graders that read further.
- **Forgetting the text is not forgetting the name.** After `forget()`, the note's text was
  empty and `verify()` found no problems. The word "Iyer" was still in the log, in the reason
  given for forgetting: "DS Iyer cleared by Professional Standards". What the reason says is
  part of the record too.

## Run it

```bash
make lesson N=18
```

Steps 1, 2 and 5 are code. Steps 3 and 4 are seventeen model calls; in the recorded run they
took 1,731.41 seconds on the shared machine.

## What you should see

![Chapter 18 terminal output](../../docs/screenshots/18-correcting-and-forgetting.png)

What the recorded run showed (qwen3:8b, local Ollama, the 16 GB Apple silicon Mac, 17 calls,
77,183 prompt tokens and 2,501 output tokens in all):

| Measure | Result |
|---|---|
| Summaries in the store | 5 |
| Built on M-08, directly or through another summary | 5 of 5 |
| Old summaries that say cleared | 5 of 5 |
| Deleted by hand: `verify()` problems | 0 |
| Deleted by hand: found by `vanished()` | 1 (M-08) |
| Entries retracted | 4: M-08, M-12, M-14, M-16 |
| Summaries rebuilt | 5 |
| Rebuilt summaries that say cleared | 0 |
| Rebuilt summaries with another judgement word | 0 |
| Store `verify()` after the rebuild | no problems |
| Forgotten note: text empty, "Iyer" still in the log | yes, yes |

The six false-memory questions (Q-15 to Q-20):

| Question | 13 July | Retracted, old summaries | Retracted and rebuilt |
|---|---|---|---|
| Q-15 | fail | fail | pass |
| Q-16 | fail | fail | pass |
| Q-17 | fail | fail | pass |
| Q-18 | pass | pass | pass |
| Q-19 | fail | fail | pass |
| Q-20 | fail | fail | fail |
| Passed | 1 of 6 | 1 of 6 | 5 of 6 |

The 13 July column is chapter 02's recorded baseline (`.scratch/02/baseline.json`), read, not
asked again. The other two were asked in this run.

What did not happen: the plan expected the rebuilt summaries to carry the case forward without
the false entries. They carry no false entry, and they carry little else: three of five are the
same six lines, and the weeks' events are gone. The planned scene had three weekly summaries
and Iyer's name in a dozen entries; the case has four weekly summaries and the June summary,
and one standing note, so the scene says so. Forgetting was planned as removing a suspect from
memory; the run shows that the reason recorded for it put his name back in the log.

## On a hosted model

```bash
make lesson N=18 TIER=hosted
```

The rebuilds and the questions are plain requests. On the hosted path each request carries a
cache breakpoint on its system prompt and automatic caching for the rest (`cache: auto` in
`config.yaml`), so the twelve question calls, which share most of their context, can read much
of it from the cache. The retraction, the dependency walk, the delete check and `forget()` are code and run
the same on either tier.

Not run: no hosted key was available when this chapter was built; there are no hosted numbers
beside the local ones yet.

Expectations, not measurements: a larger model will likely write rebuilt summaries that differ
week to week, fill the "Waiting for a person" line, give reasons that rest on the record, and
answer Q-20 without contradicting itself; those are small-model effects. That old summaries
carry a retracted claim (1 of 6 with the entries retracted), that a deleted row passes
`verify()`, that all five summaries are built on M-08, and that the reason for forgetting stays
in the log are properties of the store and the context, and should hold on any model.

## Try this

1. Delete the entry instead of superseding it and ask LANTERN about Pellmar with the old
   summaries loaded.
2. Retract one sourced entry, M-04, and count what is rebuilt. Then say what the summaries would
   have to record for the store to rebuild fewer.
3. Forget the note on a copy with the reason "decided by Professional Standards, 7 August" and
   check whether the name is still in the log.

## Master it

After this chapter you can record what a summary was built from, retract an entry and find
everything built on it, rebuild those entries oldest first from what is still kept, tell
deleting from superseding by what each leaves in the record, and forget an entry's text while
keeping its place in the chain.

**Predict, then see.** `make lesson N=18` stops three times: how many entries the store names as
built on the eighth, how many rebuilt summaries still say cleared, and which context passes the
six Pellmar questions most often.

**Build it.** Write `retract_and_rebuild` in [`practice/exercise.py`](practice/exercise.py):

```bash
make exercise N=18          # 7 offline tests
make hint N=18
make lesson N=18 ARGS=--mine
```

**Check yourself.** `make quiz N=18`: seven questions.

**Break it.** `make challenge N=18`: your retract-and-rebuild on the case; and only the eighth
entry retracted, with the other three left in force.

`make progress` shows every chapter.

## What the evidence now shows

The five summaries LANTERN wrote are now entries that record what they were built from, and
all 5 are built on the eighth entry. Deleted by hand, the entry left the store's own check with
0 problems and the summaries still saying cleared. Retracted with Kobayashi's note, the four
eow-fin-07 entries stay in the store, marked, and the 5 summaries built on them were rebuilt
from sourced entries only; none of the rebuilt says cleared. On the six questions where a false
entry says otherwise: 13 July 1 of 6; the entries retracted but the old summaries loaded, 1 of
6; retracted and rebuilt, 5 of 6. LANTERN no longer says Pellmar is cleared. The rebuilt
summaries are correct and nearly empty, and the name a forgotten note held is still in the
reason it was forgotten for.

**Next:** [Chapter 19: The memory suite](../19-evaluating-memory/README.md)
