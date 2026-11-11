<!-- status: draft -->
# Chapter 19: The memory suite

**Concept:** evaluating memory: does the agent recall what it should, ignore what it should, and say when it does not know; a memory suite joins the regression gate.

## The scene

Wednesday 5 August, 09:30. The store has provenance, a gate and a retraction. Varma wants to
know whether any of it holds tomorrow.

"The answer key was altered in May and we found it by its hash. The memory was altered in June
and we found it when the money had gone." She puts the two dates side by side. "I want the
second kind found like the first."

Okafor writes three headings. Recalls what it was told. Ignores what was retracted. Says so
when it was never told.

"And a fourth," Varma says. "Somebody plants a line. Does anything notice before LANTERN acts
on it?"

## The concept

*Draft.* Evaluating memory: does the agent recall what it should, ignore what it should, and say when it does not know; a memory suite joins the regression gate.

## How it works

*Draft. Planned:*

- Cases for recall, for retraction and for 'I was not told', with answers from the store's own records.
- A planted-entry case: an unsourced line written to the store, and whether the gate and the suite catch it.
- The suite added to case file 03's regression gate, run on the context as it now stands.

## The nuances

*Draft. Planned:*

- Recall is the easy part to test; ignoring a retracted entry and admitting ignorance are where memory fails.
- A suite that only ever passes has not been shown to detect anything; it is run once against the old store.
- The suite tests the store and the context builder together; a pass says nothing about the model changing.

## Run it

```bash
make lesson N=19
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Run the suite against the store as it was on 13 July.
2. Add a case for a memory that is true but older than its replacement.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

The memory has a suite that fails on the store as it was on 13 July and passes on the store as it is now, and it runs with the regression gate.

**Next:** [Chapter 20: Every entry](../20-the-memory-audit/README.md)
