<!-- status: draft -->
# Chapter 23: Friday 7 August

**Concept:** context in production: versioned context, a change log, a budget alarm, and the memory audit as a nightly job.

## The scene

Friday 7 August, 09:00. Professional Standards report at noon.

The context LANTERN is given now has a version, as the index did in case file 04 and the answer
key in case file 03. A change to the standing orders, the memory or the layout makes a new
version, with a name against it. The audit runs every night and its result is on Varma's desk
before she is.

At 12:10 she takes the call standing up. She listens, says "Thank you", and puts the phone down.

"He is cleared."

Then she reads this morning's audit. One write overnight, held at the gate. And a delivery note
from headquarters: something is in the loading bay for Monday.

## The concept

*Draft.* Context in production: versioned context, a change log, a budget alarm, and the memory audit as a nightly job.

## How it works

*Draft. Planned:*

- A context version: a hash over the standing orders, the tool schemas, the loaded memories and the layout, recorded with every answer.
- A change log and a budget alarm: who changed what, and a warning before the window is full.
- The audit of chapter 20 as a nightly job, with last night's result.

## The nuances

*Draft. Planned:*

- An answer without its context version cannot be reproduced; the version is part of the finding.
- An alarm nobody reads is not a control.
- A nightly audit finds what was written last night. It does not stop the writing.

## Run it

```bash
make lesson N=23
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Change one word of the standing orders and watch the version change.
2. Write an unsourced entry at night and read the morning's audit.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

LANTERN's context is versioned, logged, budgeted and audited every night, and the account that wrote the false memories is known to be a machine account that belongs to headquarters.

**Next:** Case File 07, local-models-lab: what exactly is running on LANTERN.
