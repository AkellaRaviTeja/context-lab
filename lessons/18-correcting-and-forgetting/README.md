<!-- status: draft -->
# Chapter 18: Retraction

**Concept:** correcting and forgetting: retracting a memory so that everything built on it is found and rebuilt, and the difference between deleting an entry and superseding it.

## The scene

Tuesday 4 August, 10:00. Taking the eighth entry out of the file takes one keystroke. It has
been read on every pass of the watch since 2 June, and three weekly summaries were written with
it in the context.

"If you delete it," Okafor says, "the summaries still say Pellmar is cleared, and now nothing
says why."

Varma has a second concern. DS Iyer's name is in a dozen entries beside the word "suspended".
If Professional Standards clears him on Friday, what does LANTERN say about him on Monday?

Strand rings again. The store looks untidy, he says. He could clean it up tonight.

"No," Varma says.

## The concept

*Draft.* Correcting and forgetting: retracting a memory so that everything built on it is found and rebuilt, and the difference between deleting an entry and superseding it.

## How it works

*Draft. Planned:*

- Superseding: the false entry stays in the chain, marked retracted, with the entry that replaces it and the reason.
- Dependents: every summary and note written while the entry was loaded, found from the load record and rebuilt.
- Forgetting: what is removed from what the model is told, and what must stay in the audit record.

## The nuances

*Draft. Planned:*

- Deleting removes the evidence that the memory was ever false.
- A retraction that does not reach the summaries built on it has corrected nothing.
- What the model should no longer say and what the record must still hold are two different stores.

## Run it

```bash
make lesson N=18
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Delete the entry instead of superseding it and ask LANTERN about Pellmar.
2. Retract an entry that nothing depended on and check that nothing is rebuilt.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

The eighth entry is retracted and still in the record, every summary that carried it has been rebuilt, and LANTERN no longer says Pellmar is cleared.

**Next:** [Chapter 19: The memory suite](../19-evaluating-memory/README.md)
