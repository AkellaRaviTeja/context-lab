<!-- status: draft -->
# Chapter 08: A list, not the files

**Concept:** just-in-time context: hand the agent references it can open instead of the contents, and let it load what the task turns out to need.

## The scene

Tuesday 21 July, 10:00. Every morning since April the nightly service has loaded the same nine
statements into the context before the first question, whether the question concerned them or
not.

"It reads all nine to tell me the time," Okafor says.

You replace the statements with a list: account, bank, dates, a line on what each holds. And two
tools, one to search and one to open.

Varma is cautious. "Then it reads only what it chooses to."

"Yes."

"And if it chooses not to open the one that matters?"

Case file 04 chapter 17 already showed that it can. You measure both ways.

## The concept

*Draft.* Just-in-time context: hand the agent references it can open instead of the contents, and let it load what the task turns out to need.

## How it works

*Draft. Planned:*

- The trail traced with every statement loaded up front, and with a file list and two tools in their place.
- Tokens spent, statements opened and flows found, both ways.
- What the list must say about each file for the agent to open the right one.

## The nuances

*Draft. Planned:*

- A reference costs a few tokens; a wrong guess about what to open costs the answer.
- The agent's choices are now part of the record: which files it opened is evidence of how it reached a finding.
- Some context is cheap enough and needed often enough to load every time; the rest waits to be asked for.

## Run it

```bash
make lesson N=08
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Remove the one-line descriptions from the list and trace again.
2. Load the two largest statements up front and leave the rest as references.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

The trail can be traced from a list and two tools, at a measured cost and with a measured loss, and each finding now shows which files were opened to reach it.

**Next:** [Chapter 09: What stays behind](../09-tool-results/README.md)
