<!-- status: draft -->
# Chapter 07: Merely related

**Concept:** distraction: documents that are true and related but not needed make answers worse, so what is left out of the context is a decision with a measured effect.

## The scene

Monday 20 July, 09:40. Mensah's instinct is the careful officer's instinct: give it everything
about Pellmar. Every statement, every minute, every email that names it.

"More to go on," she says.

You run the question with the one statement that answers it. Then with five more pages that
mention Pellmar and do not. Then ten.

The answer changes on the way. Nothing false was added. Every page is real and every page is
about Pellmar.

"So which one misled it?" Mensah asks.

"None of them is wrong," you say. "They are in the way."

## The concept

*Draft.* Distraction: documents that are true and related but not needed make answers worse, so what is left out of the context is a decision with a measured effect.

## How it works

*Draft. Planned:*

- One question with its answering document, then with true, related, unneeded pages added a few at a time.
- The point at which the answer first changes, and what it changes to.
- A relevance cut-off for the context builder, scored against the baseline.

## The nuances

*Draft. Planned:*

- Related material distracts more than unrelated material: it looks like an answer.
- The model rarely says it was given too much.
- Leaving a document out is a decision someone must be able to defend; the builder records what it left out.

## Run it

```bash
make lesson N=07
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Add ten pages about an unrelated company instead. Is the effect the same?
2. Put the answering document last among the distractors.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

Adding true pages changed an answer, at a count that is now known, and the context builder leaves out what a question does not need and says what it left out.

**Next:** [Chapter 08: A list, not the files](../08-just-in-time/README.md)
