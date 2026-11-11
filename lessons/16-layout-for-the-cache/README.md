<!-- status: draft -->
# Chapter 16: The same beginning

**Concept:** layout for the cache: a model server reuses its work on a prompt's unchanged beginning, so stable parts go first, changing parts last, and the saving is measured in time.

## The scene

Friday 31 July, 08:45. Varma's first question each morning takes the best part of a minute to
begin answering. The second, straight after, starts almost at once.

"Why is it slow only when I arrive?"

Case file 02 chapter 20 found one cause: a timestamp in the system prompt, new every request,
so that nothing after it could be reused.

The cause this morning is the nightly sync. It rewrites the first lines of the context at
01:58 each night.

"So every morning it reads everything again from the top," Okafor says.

"From the first thing that changed," you say.

## The concept

*Draft.* Layout for the cache: a model server reuses its work on a prompt's unchanged beginning, so stable parts go first, changing parts last, and the saving is measured in time.

## How it works

*Draft. Planned:*

- Ollama's reuse of an unchanged prefix, measured: prompt evaluation time for a cold request, a repeat, and a request that differs only at the end.
- A change at the start, the middle and the end of the context, and what each costs in seconds.
- The builder's layout: rules and tool schemas first, memory next, evidence and the question last, with the times before and after.

## The nuances

*Draft. Planned:*

- On Ollama the cache saves time, not counted tokens: prompt_eval_count reports the full prompt whatever was reused.
- The cache holds one prefix per loaded model slot; another conversation in between evicts it.
- Cache order and answer order pull against each other; chapter 06's layout is checked again here.

## Run it

```bash
make lesson N=16
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Put the date at the top of the system prompt and measure.
2. Ask two different officers' questions alternately and watch the reuse disappear.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

The context is laid out so its unchanged beginning is reused, and the time that saves on LANTERN is measured, not assumed.

**Next:** [Chapter 17: Four ways to be wrong](../17-how-context-fails/README.md)
