# 0001: TOON is one row in chapter 05

Status: Accepted, 11 November 2026 (the author chose the recommended option).

## Context

Chapter 05 compares ways to serialise the same records. The plan asked whether TOON earns a
chapter of its own beside the common formats.

Measured with `spikes/formats.py`: the 31 payments from Halcyon to Northwind (five fields each),
one system line, ten questions with answers computed from the rows (four amounts by reference,
three references by date and amount, the count, a count by payer account, the largest payment),
qwen3:8b at temperature 0, seed 7, thinking off.

| Format | Characters | Prompt tokens | Right of 10 |
|---|---|---|---|
| JSON, indented | 5,489 | 2,350 | 7 |
| JSON, compact | 4,372 | 1,762 | 7 |
| YAML | 4,278 | 1,945 | 8 |
| Markdown table | 2,654 | 1,503 | 8 |
| TOON | 2,325 | 1,497 | 8 |
| CSV | 2,248 | 1,429 | 7 |

Every format got the seven lookups right. No format named the largest payment. Asked how many
payments are listed, every format but TOON answered 30; TOON, whose header declares `[31]`,
answered 31.

## Options

1. One row in chapter 05's table. TOON costs 5% more tokens than CSV on these rows and differs
   from it in one behaviour.
2. Its own chapter. More depth on one young format, and every later chapter renumbers.
3. Leave it out.

## Decision

Option 1. TOON is a sixth format in chapter 05. Its declared length is a nuance of that chapter
and a candidate challenge.

## Consequences

- The lab stays at 23 chapters.
- Chapter 05 writes TOON for uniform rows by hand (a header and comma-separated lines), so no
  TOON package is a dependency. Nested records are out of scope and the chapter says so.
- These figures are a spike on ten questions. Chapter 05's figures come from its own recorded
  run and may differ.
- Would change the decision: a recorded run in which TOON's accuracy differs from CSV's and the
  Markdown table's by more than its question count can explain.
