<!-- status: draft -->
# Chapter 09: What stays behind

**Concept:** tool results in the history: a result is read once and then carried on every later turn, so results are trimmed, summarised or cleared once used.

## The scene

Wednesday 22 July, 09:30. One call to the statement tool returns Arden's whole quarter. The
agent needed one line of it.

Okafor follows the trace turn by turn. The quarter is there on turn two, where it was asked
for. It is there again on turn three, and on turn nine.

"It is carrying Arden everywhere it goes," he says.

By the last turn most of what LANTERN is reading is statements it has finished with. Case file
02 chapter 20 counted the cost in tokens. Nobody has yet asked what it costs in attention.

"Can it put them down?" Varma asks.

## The concept

*Draft.* Tool results in the history: a result is read once and then carried on every later turn, so results are trimmed, summarised or cleared once used.

## How it works

*Draft. Planned:*

- One trace, with the share of each request that is old tool results, turn by turn.
- Three treatments of a used result: trim to the lines asked for, replace with a summary, clear with a note of where to find it again.
- Each scored on tokens and on flows found.

## The nuances

*Draft. Planned:*

- A cleared result must leave a line saying it was cleared, or the model will act as if it never looked.
- A summary of a result is a new document that someone wrote; it can be wrong.
- Trimming at the tool is safer than trimming afterwards: what was never returned cannot be mistaken for the whole.

## Run it

```bash
make lesson N=09
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Clear results after one turn instead of three.
2. Summarise with the small model and compare what survives.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

Old tool results no longer travel with the agent to the end of a run, and what each treatment saved and lost is measured.

**Next:** [Chapter 10: Who paid whom](../10-compaction-with-a-schema/README.md)
