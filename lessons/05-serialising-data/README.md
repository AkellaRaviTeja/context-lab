<!-- status: draft -->
# Chapter 05: Thirty-one payments, five ways

**Concept:** serialisation: the same records cost different numbers of tokens as JSON, YAML, a Markdown table, CSV and TOON, and the model does not read every format equally well.

## The scene

Thursday 16 July, 09:00. Halcyon paid Northwind thirty-one times. Those thirty-one rows have
been in front of LANTERN since April, always in the same shape: the JSON the bank tool returns.

Okafor has never liked it. "Every row says 'amount' again. Thirty-one times. I would not pay a
clerk to write that."

You show him the same rows as a table, then as comma-separated lines.

"Smaller," he says. "Does it still read the right cell?"

That is the question. A format that saves a third of the window and misreads one amount in
thirty-one has saved nothing the court can use.

## The concept

*Draft.* Serialisation: the same records cost different numbers of tokens as JSON, YAML, a Markdown table, CSV and TOON, and the model does not read every format equally well.

## How it works

*Draft. Planned:*

- The thirty-one payments in each format, counted with the model's tokenizer.
- The same lookup, filter and sum questions asked of each format, with answers from the statements.
- Tokens against accuracy, format by format, on this model.

## The nuances

*Draft. Planned:*

- The saving depends on the shape of the data: uniform rows compress, nested records do not.
- A format the model has seen less of may cost fewer tokens and more mistakes.
- Arithmetic belongs in a tool whatever the format; case file 02 chapter 01 settled that.

## Run it

```bash
make lesson N=05
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Sort the rows by amount instead of date and ask the same questions.
2. Drop the header row from the CSV. What does the model make of the columns?

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

The thirty-one payments have a measured cost and a measured error rate in each format, and the context builder has a default chosen from those two numbers.

**Next:** [Chapter 06: The middle](../06-order-and-placement/README.md)
