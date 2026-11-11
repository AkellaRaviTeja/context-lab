<!-- status: draft -->
# Chapter 14: What to load

**Concept:** reading from memory: which entries are loaded at the start of a session, by case, by recency and by relevance, and how many is too many.

## The scene

Wednesday 29 July, 09:30. The store is clean and it is growing. Four months of inquiry will be
several hundred entries by the autumn.

"Load them all," Mensah says. "It is only memory."

Chapter 07 is still on the whiteboard: true, related, in the way.

You try it three ways. Everything for this case. The most recent twenty. The twenty closest to
the question. Okafor adds a fourth column on his own: the entries a person would have chosen.

None of the three matches his column.

"Which did it need?" Varma asks. "And did it get them?"

## The concept

*Draft.* Reading from memory: which entries are loaded at the start of a session, by case, by recency and by relevance, and how many is too many.

## How it works

*Draft. Planned:*

- The store loaded by case, by recency and by relevance to the question, at several sizes.
- Each scored on the baseline: did the answer need an entry that was not loaded, or suffer from one that was.
- A loading rule for the builder, with procedures always present and facts fetched on need.

## The nuances

*Draft. Planned:*

- Recency favours the newest entry, and the newest entry is the one least checked.
- Relevance by embedding finds entries about the same thing, not entries that agree; case file 04 chapter 02.
- An entry that is not loaded does not exist for that session; the builder records what it loaded.

## Run it

```bash
make lesson N=14
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Load the hundred most relevant entries instead of twenty.
2. Ask a question whose answer depends on the oldest entry in the store.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

Each session now starts with a chosen set of memories, the choice is recorded, and the cost of loading too many is measured.

**Next:** [Chapter 15: Forty statements, five lines](../15-isolating-context/README.md)
