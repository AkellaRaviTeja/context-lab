<!-- status: draft -->
# Chapter 04: Four months of standing orders

**Concept:** the system prompt as a maintained document: rewritten from observed failures, with every rule traceable to the reason it exists, and scored against the baseline.

## The scene

Wednesday 15 July, 10:30. The standing orders began in March as Varma's one rule: cite the
evidence or say "not in evidence". You print today's version. It runs to pages.

Okafor goes through it with two pens. Rules added after a failure, in blue. Rules nobody can
explain, in red.

"This one says always give totals in the currency of the statement," he says. "This one, a page
later, says never state a currency." He caps the red pen. "Which does it follow?"

"Whichever it read last," you say. "Or neither."

Varma wants it shorter. She also wants proof that shorter is not worse.

## The concept

*Draft.* The system prompt as a maintained document: rewritten from observed failures, with every rule traceable to the reason it exists, and scored against the baseline.

## How it works

*Draft. Planned:*

- The versions of the standing orders from March to July, and what each added.
- Each rule checked against the failure it was written for; rules with no failure behind them listed.
- A rewrite, scored against the baseline on the same questions and seed.

## The nuances

*Draft. Planned:*

- A rule added for one failure is read on every question from then on.
- Two rules that contradict each other do not cancel; the model picks, and not always the same way.
- A shorter prompt that scores the same is the better prompt: it leaves room and it can be read.

## Run it

```bash
make lesson N=04
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Delete one rule you believe is essential and run the baseline.
2. Move Varma's first rule from the top to the bottom and compare.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

The standing orders are one page with a reason beside every rule, and the baseline says what the rewrite cost and what it bought.

**Next:** [Chapter 05: Thirty-one payments, five ways](../05-serialising-data/README.md)
