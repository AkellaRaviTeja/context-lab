<!-- status: draft -->
# Chapter 03: Who is spending the window

**Concept:** the token budget: the window is a fixed sum, every section of the context spends from it, and the spending is measured, not guessed.

## The scene

Tuesday 14 July, 09:10. Okafor reads a context the way he reads a ledger: who is spending, and
on what.

You give him the count from Monday as one number. He hands it back.

"A total tells me nothing. I want it by account." He draws columns: standing orders, memory,
summaries, tool descriptions, history, evidence, the question. "And I want to know what is left
for the answer."

Varma, passing: "And what happens when it does not balance."

You know the answer to that one from case file 01. Nothing happens. The oldest part goes
missing and nobody is told.

## The concept

*Draft.* The token budget: the window is a fixed sum, every section of the context spends from it, and the spending is measured, not guessed.

## How it works

*Draft. Planned:*

- Tokens by section, counted with the model's tokenizer, for the context as it stands on 13 July.
- A budget: a limit per section and for the whole, with room reserved for the answer.
- An over-budget context refused in code before it is sent, with the section that broke it named.

## The nuances

*Draft. Planned:*

- A count by words or characters is wrong by a different amount for prose, JSON and account numbers.
- Tool schemas are paid on every request whether or not a tool is called.
- The reply and the model's thinking spend from the same window as the input.

## Run it

```bash
make lesson N=03
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Find the largest section and halve it. What does the baseline score do?
2. Set the answer reserve to zero and watch what an over-full request returns.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

The window has an account for each section, and the sections that take the most are known. The context builder now refuses a request that would not fit.

**Next:** [Chapter 04: Four months of standing orders](../04-rewriting-the-system-prompt/README.md)
