<!-- status: draft -->
# Chapter 15: Forty statements, five lines

**Concept:** isolating context: a sub-agent reads at length in a context of its own and returns a few lines, so the main context never holds what it read.

## The scene

Thursday 30 July, 10:20. Ostrander Marine Finance received 296,400.00 on 24 June, and the bank
has now produced forty daily statements for the client account it came from.

Reading forty statements in the main context would leave room for little else.

"Send someone to read them," Varma says, "and have them report."

That is what a sub-agent is. It reads all forty in a window of its own and hands back five
lines. Case file 02 chapter 18 measured what teams of agents cost. This is a smaller question.

Okafor asks it. "What was in the other thirty-five pages that it decided I did not need?"

## The concept

*Draft.* Isolating context: a sub-agent reads at length in a context of its own and returns a few lines, so the main context never holds what it read.

## How it works

*Draft. Planned:*

- One agent reading forty statements in its own context, and the same task through a sub-agent that returns a short report.
- Tokens in the main context, and answers to follow-up questions, both ways.
- What the report must carry (sources, what was not read) for the main agent to rely on it.

## The nuances

*Draft. Planned:*

- Isolation saves the main window and hides the detail; a follow-up question may need what was left behind.
- The report is testimony: the main agent cannot check it without reading the statements itself.
- The sub-agent needs its task written out in full; it has none of the main context.

## Run it

```bash
make lesson N=15
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Ask the main agent a question the report does not cover.
2. Have the sub-agent return ten lines instead of five and compare.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

Forty statements were read without entering the main context, and what the five-line report kept and lost is measured.

**Next:** [Chapter 16: The same beginning](../16-layout-for-the-cache/README.md)
