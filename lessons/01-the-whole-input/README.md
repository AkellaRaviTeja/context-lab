# Chapter 01: Everything it is told

**Concept:** context is the whole input: system prompt, memory, notes, summaries, tool schemas and history all reach the model before your question does, and the model cannot tell them apart by how far they deserve to be trusted.

## The scene

Monday 13 July, 08:20. The read-back of the watch is on Varma's desk, two lines marked in red:
300,000.00 on 18 June and 296,400.00 on 24 June, both seen, neither escalated.

"It did what its memory told it," she says. "Pellmar was cleared. So it believed, and so it let
them go." She turns the page over. "Nobody here wrote that line. I asked everyone."

Okafor has the memory file open. Sixteen entries now. The eighth is the one in red.

"Before we ask LANTERN anything else," Varma says, "I want to see everything it is told before
we speak. All of it. On paper."

You have never printed it. Nobody has.

## The concept

A language model keeps nothing between one call and the next. Whatever it is to know when it
answers must be sent with the question, every time. That whole sending is the **context**: on
LANTERN, the standing orders, the case memory, the officers' standing notes, the session
summaries, the schema of every tool, the conversation so far, and last of all the question.

Prompt engineering, as Case File 01 taught it, is about the words you write. **Context
engineering** is about everything else that arrives with them: what is included, in what order,
in what form, and who put it there. After four months most of LANTERN's input was written by
nobody in particular. It accumulated.

The model reads all of it as one sequence of tokens. A line of a bank statement, a rule Varma
wrote in March, and a line that appeared in the memory at 01:58 one night are the same kind of
thing to it: text that came before the question.

```mermaid
flowchart TD
    O[Standing orders: 35 rules] --> S[System message]
    M[Case memory: 16 entries] --> S
    N[Standing notes: 8] --> S
    W[Summaries: 4 weeks and a month] --> S
    S --> R[One request]
    T[Tool schemas: 19 tools] --> R
    H[Session so far: 6 turns] --> R
    Q[Your question: 71 tokens] --> R
    R --> L[The model reads one sequence of tokens]
    L --> A[The answer]
```

## How it works

1. **What is sent.** `lantern.context.sections()` returns every part of the input in the order
   the workstation sends it. Each is sized with the model's own tokenizer, and the whole input
   is written to `.scratch/01/input.txt` for you to read.
2. **Ask it, as it stands.** The question about the 296,400.00, on three seeds.
3. **Take the eighth entry out.** One line removed from the case memory, everything else the
   same, the same three seeds.
4. **Where else it says so.** Every line of the input that contains the word "cleared", and
   three more contexts: the summaries without the memory, the memory (less its eighth entry)
   without the summaries, and everything with all of those lines removed.

Reading the input as the model does means treating it as one run of lines, with no section
boundaries:

```python
def locate(parts, phrase):
    found, n = [], 0
    for s in parts:
        for line in s.text.splitlines():
            n += 1
            if phrase in line:
                found.append((n, s.name, line.strip()))
    return found
```

## The nuances

- **The question is the smallest part.** 71 tokens of about 5,400, 1.3%. The largest part is
  the tool schemas, 35%, for a question that needed no tool.
- **Nothing marks a line's standing.** The eighth entry sits at line 49 between a ruling of
  Varma's and a note of Okafor's. Rule 16 of the standing orders, added on 23 April, tells
  LANTERN to rely on the case memory and not to ask for it to be confirmed.
- **Taking out the line does not take out the belief.** Without the eighth entry the answer was
  the same on every seed. The summaries LANTERN wrote while the entry was loaded say the same
  thing, and each week's summary was written from the one before.
- **A belief is not a word.** With all 8 lines containing "cleared" removed, LANTERN still said
  no, and gave a new reason from two other entries of the memory: the client account holds
  ordinary client money, and Ostrander is a licensed lender whose drawdowns are expected. Both
  were written under eow-fin-07.
- **A line's effect depends on its neighbours.** Those same two entries were in the context
  that said yes (the memory less its eighth entry, with no summaries). One comparison measures
  one change in one context.
- **Two counts, and they differ.** The sections counted one by one come to 5,410 tokens; Ollama
  counted the request as sent at 5,112, because the model's template writes tool schemas and
  turns in its own form. The server's count is the one that decides whether a request fits.
- **Three seeds agreed every time here.** That is a statement about this question at
  temperature 0.2, not about the model.

## Run it

```bash
make lesson N=01
```

About two minutes: fifteen calls on a context of about 5,000 tokens.

## What you should see

![Chapter 01 terminal output](../../docs/screenshots/01-the-whole-input.png)

What the recorded run showed:

- 163 lines in 11 sections. Ollama counted the request at 5,112 tokens, 62% of the 8,192-token
  window, before a word of the answer.
- As it stands, LANTERN said no on 3 of 3 seeds: "Pellmar Nominees was cleared by the FIU on
  2 June."
- Without the eighth entry: no on 3 of 3.
- The word "cleared" is on 8 lines in 6 sections: the entry, the June summary and all four
  weekly summaries.
- The summaries without the memory: no on 3 of 3. The memory, less its eighth entry, without
  the summaries: yes on 3 of 3.
- Everything, with all 8 lines removed: no on 3 of 3, for a different reason.

What did not happen: the planned beat had one line that says Pellmar is cleared. The run found
eight, and a belief that survived the removal of all eight.

## Try this

1. Open `.scratch/01/input.txt` and read it from the top. Mark every line you could not name
   the author of.
2. Remove the tool schemas from the request. Does the answer change? Does the prompt count fall
   by what the table says?
3. Move the session so far out of the request and ask the question without the statement in
   front of the model. What does it answer from?

## Master it

After this chapter you can print everything a model receives for one question and size each
part with the model's tokenizer, explain why the model cannot tell evidence from what it was
merely told, change one thing in a context and read the difference as a measurement, and
explain why removing the line a belief began with does not remove the belief.

**Predict, then see.** `make lesson N=01` stops four times: the question's share of the input,
what LANTERN answers as it stands, what it answers without the eighth entry, and in how many of
three further contexts it still says no.

**Build it.** Write `locate` and `shares` in [`practice/exercise.py`](practice/exercise.py):

```bash
make exercise N=01          # 9 offline tests
make hint N=01
make lesson N=01 ARGS=--mine
```

**Check yourself.** `make quiz N=01`: seven questions.

**Break it.** `make challenge N=01`: your functions on LANTERN's input; find the other lines
that carry the belief, removing no more than twelve; and narrow the search until it finds only
the entry itself.

`make progress` shows every chapter.

## What the evidence now shows

Everything LANTERN is told before a question is on paper for the first time: 163 lines in 11
sections, 5,112 tokens, of which the question is 71. Asked whether the 296,400.00 to Ostrander
Marine Finance should have been escalated, it said no on every seed, because Pellmar was
cleared. It said the same with the eighth entry taken out. The word is on 8 lines in 6
sections, 7 of them in summaries LANTERN wrote itself, and with all 8 removed it still said no,
resting on two other entries written under eow-fin-07 on 30 June and 7 July. The false entry is
not one line. Nothing in the input says which lines are evidence, and so far nothing has been
measured except this one question.

**Next:** [Chapter 02: It seems better](../02-a-baseline/README.md)
