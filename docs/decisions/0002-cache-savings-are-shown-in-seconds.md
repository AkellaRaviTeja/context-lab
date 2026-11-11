# 0002: Cache savings are shown in seconds

Status: Proposed, 11 November 2026. A choice of method made by the build from the measurement
below; the author has not been asked and may change it.

## Context

Chapter 16 teaches laying a context out so the model server can reuse its work. On a hosted API
the saving shows as cached tokens on the bill. Case File 02 chapter 20 found that Ollama reports
no such thing: the cache saves time, not counted tokens. The plan asked how this lab shows the
saving.

Measured with `spikes/cache.py`: one system line and 55 rows of Arden's statement (about 3,340
prompt tokens), 20 tokens of output, three rounds, each round with a fresh marker in the system
line so nothing is reused between rounds.

| Request | Prompt tokens reported | Prompt evaluation, seconds (three rounds) |
|---|---|---|
| Cold | 3,343 | 16.23, 16.23, 16.24 |
| Exact repeat | 3,343 | 0.05, 0.05, 0.05 |
| Same beginning, new question at the end | 3,344 | 0.19, 0.19, 0.19 |
| A timestamp at the top | 3,366 | 16.42, 16.39, 16.38 |
| A new timestamp at the top, again | 3,363 | 16.24, 16.27, 16.24 |
| Same beginning, after an unrelated short conversation | 3,341 | 0.18, 0.19, 0.19 |

`prompt_eval_count` is the full prompt every time. `prompt_eval_duration` falls from 16.2 s to
0.2 s when only the end changes, and does not fall at all when the first line changes. One short
unrelated conversation in between did not evict the prefix on this version of Ollama.

A first attempt at the measurement used 150 rows. The prompt was over the server's limit, was
cut to 4,098 tokens without a word, and gave timings that meant nothing. The spike keeps the
prompt well inside the window, and chapter 16 must do the same.

## Options

1. Report `prompt_eval_duration` in seconds for each layout, with `prompt_eval_count` beside it
   to show that the count does not move. Three rounds each.
2. Report wall-clock time to first token. It is what a person feels, and it mixes in model
   loading and output.
3. Run the chapter on a hosted API that reports cached tokens. Evidence would leave the building.

## Decision

Option 1. Chapter 16 reports prompt evaluation seconds, three rounds per layout, with the token
count shown unchanged beside them and the share of the prompt that had to be read again worked
out from the two. Wall-clock time is shown once, for the scene.

## Consequences

- Chapter 16's numbers are times, so they vary by machine. The README says which machine, and
  the challenges compare ratios, not seconds.
- Every prompt in the chapter is checked to be inside the window before it is timed.
- The draft nuance "another conversation in between evicts it" was not borne out by this spike
  and is rewritten from chapter 16's own run.
- Would change the decision: an Ollama release that reports reused tokens in its response.
