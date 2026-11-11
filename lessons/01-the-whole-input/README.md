<!-- status: draft -->
# Chapter 01: Everything it is told

**Concept:** context is the whole input: system prompt, memory, tool schemas and history all reach the model before your question does, and the model cannot tell them apart by how far they deserve to be trusted.

## The scene

Monday 13 July, 08:20. The read-back of the watch is on Varma's desk, two lines marked in red:
300,000.00 on 18 June and 296,400.00 on 24 June, both seen, neither escalated.

"It did what its memory told it," she says. "Pellmar was cleared. So it believed, and so it let
them go." She turns the page over. "Nobody here wrote that line. I asked everyone."

Okafor has the memory file open. Eight entries. He knows the hand behind seven of them.

"Before we ask LANTERN anything else," Varma says, "I want to see everything it is told before
we speak. All of it. On paper."

You have never printed it. Nobody has.

## The concept

*Draft.* Context is the whole input: system prompt, memory, tool schemas and history all reach the model before your question does, and the model cannot tell them apart by how far they deserve to be trusted.

## How it works

*Draft. Planned:*

- Capture the exact request LANTERN sends for one question: every message, every tool schema, every option.
- Count it, section by section, with the model's own tokenizer.
- Read it as the model does: one flat sequence, with nothing to say which lines came from evidence.

## The nuances

*Draft. Planned:*

- The question is the smallest part of what the model reads.
- Nothing in the input marks a memory entry as less certain than a standing order.
- What is over the window is dropped without a word; case file 01 chapter 03 showed which end.

## Run it

```bash
make lesson N=01
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Print the request for a one-word question and find your question in it.
2. Remove the memory file and ask whether Pellmar should be escalated.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

Everything LANTERN is told before a question is on paper for the first time, with its length, and the eighth entry of the case memory is in it, looking like every other line.

**Next:** [Chapter 02: It seems better](../02-a-baseline/README.md)
