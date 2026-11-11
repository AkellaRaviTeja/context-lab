<!-- status: draft -->
# Chapter 11: Its own notes

**Concept:** structured notes outside the window: the agent writes down flows found and questions open, and reads them back after a compaction or a restart.

## The scene

Friday 24 July, 09:00. A detective who loses her notebook starts the interview again. LANTERN,
after a compaction, has only what the summary kept.

"Give it a notebook," Mensah says.

Case file 02 gave it a memory file, and the file kept its mistakes along with its findings. This
is narrower: working notes for one task, in a form code can read, kept outside the window and
opened when needed.

Varma asks the only question she ever asks about a new record. "Who can write in it?"

"The agent. Only for this run. And every line says which tool result it came from."

"Then I can check it," she says.

## The concept

*Draft.* Structured notes outside the window: the agent writes down flows found and questions open, and reads them back after a compaction or a restart.

## How it works

*Draft. Planned:*

- A notes tool: add a flow, add an open question, close a question, each with its source.
- A long trace with a compaction in the middle, with and without the notes.
- The notes read back after a restart, and the run carried on from them.

## The nuances

*Draft. Planned:*

- Notes are context the agent wrote for itself; a wrong note is believed more readily than a wrong document.
- A note without a source cannot be checked and is refused.
- Notes are for one task. What deserves to outlive the task is a memory, and that is a different decision.

## Run it

```bash
make lesson N=11
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Let the agent write free-text notes instead and compare what it can recover.
2. Corrupt one note by hand and see whether the agent catches it.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

The agent carries on after a compaction from notes it wrote itself, each tied to the tool result behind it.

**Next:** [Chapter 12: A fact with no episode](../12-kinds-of-memory/README.md)
