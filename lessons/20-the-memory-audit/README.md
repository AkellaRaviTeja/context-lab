<!-- status: draft -->
# Chapter 20: Every entry

**Concept:** the memory audit: every entry traced to its source, its author and the session that wrote it, across the store's whole history.

## The scene

Thursday 6 August, 08:30. Professional Standards report tomorrow. DS Iyer has been at home
since May, his badge in a drawer at headquarters.

The audit runs over every write the memory store has ever taken. Most trace to a statement, a
ruling, a signed file.

A set do not. Okafor lays them out by date, and then lays Iyer's suspension beside them.

"These were written under his account."

"After he surrendered his badge," Varma says. "Some of them."

She does not say what that means. She asks for the session records behind each write: the
machine it came from, and the account that opened the connection.

## The concept

*Draft.* The memory audit: every entry traced to its source, its author and the session that wrote it, across the store's whole history.

## How it works

*Draft. Planned:*

- Every entry joined to its source document, its author and the session that wrote it.
- The entries with no source, by date, against DS Iyer's suspension and badge records.
- The session records behind those writes, and the account that opened each connection.

## The nuances

*Draft. Planned:*

- A login name on an entry says which account was used, not who used it.
- The audit can show that an account wrote after its holder could not have; it cannot show intent.
- The audit is only as good as the logs it joins, and somebody administers those logs.

## Run it

```bash
make lesson N=20
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Audit only the entries about Pellmar and Tidewater.
2. Remove the session log and see how far the audit gets on the store alone.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

Every entry in LANTERN's memory is traced or listed as untraceable, and the untraceable ones were written under an account whose holder had surrendered his badge.

**Next:** [Chapter 21: Memory in a box](../21-frameworks-review/README.md)
