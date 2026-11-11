<!-- status: draft -->
# Chapter 10: Who paid whom

**Concept:** compaction with a schema: a summary of the history has named fields that must survive, and code checks them after every compaction.

## The scene

Thursday 23 July, 10:10. Varma has not forgotten April. Three days of tracing, a compacted
history, and a summary that kept the amounts and lost which account paid which.

"It summarised the trail into a list of numbers," she says. "Tell me that cannot happen again."

You cannot tell her that about a paragraph the model writes freely. You can about a form.

Okafor drafts it on the whiteboard as he would a schedule: payer, payee, total, count, the
statement it came from. Open questions. Accounts not yet read.

"If a line has no payer," he says, "it is not a line."

## The concept

*Draft.* Compaction with a schema: a summary of the history has named fields that must survive, and code checks them after every compaction.

## How it works

*Draft. Planned:*

- Case file 02's free-text compaction on a long trace, and what it loses.
- A schema for the compacted state: flows with payer, payee, total and source; open questions; accounts read.
- A check in code after each compaction, and what happens when it fails.

## The nuances

*Draft. Planned:*

- A summary is written by the model that will read it; it can drop a field and never notice.
- The check proves the fields are present and match the tool results, not that nothing else of value was lost.
- Summaries of summaries lose more each time; compacting from the source avoids it.

## Run it

```bash
make lesson N=10
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Compact twice in a row and compare the second summary with the first.
2. Remove 'source' from the schema and see which flows can no longer be checked.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

A compaction either keeps who paid whom, checked in code against the tool results, or is refused and done again.

**Next:** [Chapter 11: Its own notes](../11-notes-and-scratchpads/README.md)
