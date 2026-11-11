<!-- status: draft -->
# Chapter 13: Who may write

**Concept:** writing to memory: every entry carries a source document, an author, a time and a hash, and an entry without a source waits for a person.

## The scene

Tuesday 28 July, 10:00. Until today, anything with access to the file could add a line to it.
The watch could. The nightly service could. Any account on the team could.

Varma has the write history in front of her, the eighth entry underlined.

"I want four things on every entry. Where it came from. Who wrote it. When. And a way to know
it has not been changed since."

Strand has rung twice this week. He has heard about the audit and offers to clean up the memory
store for the team, to save you the trouble.

"Thank him," Varma says. "And tell him nothing is to be touched."

## The concept

*Draft.* Writing to memory: every entry carries a source document, an author, a time and a hash, and an entry without a source waits for a person.

## How it works

*Draft. Planned:*

- A memory store in SQLite: entry, kind, source document, author, time, and a hash chained to the entry before it.
- A write gate: an entry whose source does not exist, or does not say what the entry claims, is held for a person.
- The eight entries replayed through the gate, to see which are held.

## The nuances

*Draft. Planned:*

- The model proposing a memory is not a source; the tool result or document it read is.
- A hash chain shows that something changed, not who changed it or why.
- A gate that holds everything will be switched off; it must pass what is plainly sourced.

## Run it

```bash
make lesson N=13
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Write an entry whose source exists but says the opposite.
2. Change one stored entry by hand and verify the chain.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

Nothing enters LANTERN's memory without a source, an author, a time and a place in the chain, and the entry that started this inquiry would have been held.

**Next:** [Chapter 14: What to load](../14-reading-from-memory/README.md)
