# Chapter 04: Four months of standing orders

**Concept:** the system prompt as a maintained document: rewritten from observed failures, with every rule traceable to the reason it exists, and scored against the baseline.

## The scene

Wednesday 15 July, 10:30. The standing orders began in March as three rules, one of them
Varma's: cite the evidence or say "not in evidence". You print today's version. Thirty-five.

Okafor goes through it with two pens. Rules added after a failure, in blue. Rules that
disagree with another rule, in red.

"This one says always give amounts with their currency," he says. "This one, fourteen rules
later, says never state a currency." He caps the red pen. "Which does it follow?"

"Whichever it read last," you say. "Or neither."

"That is a guess." He writes it down as one.

Varma wants it shorter. She also wants proof that shorter is not worse.

## The concept

A **system prompt** is the part of the context a team writes on purpose. On LANTERN it is the
standing orders. It is also the part most likely to grow without being read: a failure
happens, somebody adds a rule, and the rule is sent with every question from then on.

Treating the prompt as a **maintained document** means four things:

- **It has a history.** Each rule has a date, an author and the failure it was written for.
- **It is read against itself.** Two rules that disagree do not cancel and do not raise an
  error. The model settles the clash somehow, and nobody is told how.
- **It is rewritten, not only extended.** A rewrite groups the rules, settles the clashes in
  writing and drops what no longer applies.
- **Every version is scored.** A rewrite is a change to the context. It goes through the
  baseline like any other.

```mermaid
flowchart LR
    F[A failure is seen] --> A[A rule is added]
    A --> G[35 rules, never read as a whole]
    G --> L[Lint and read: which rules disagree?]
    L --> M[Measure: which does the model follow?]
    M --> W[Rewrite from the failures]
    W --> S[Score against the baseline]
    S -- worse --> W
    S -- no worse --> K[Propose it, with what it fixed and broke]
```

## How it works

1. **How it grew.** The 31 versions under `case/state/standing-orders/`, with the change log
   that says who added each rule and why.
2. **Read it for rules that disagree.** A lint pairs rules that share a term where one demands
   and the other forbids.
3. **Which does it follow?** Two questions on three seeds, with the orders as they stand and
   with each clashing pair in each other's places.
4. **The rewrite, scored.** `case/rebuilt/standing-orders.md` in place of the standing orders,
   on all 26 signed questions.
5. **What a rule cannot do.** The six questions the false entries decide, under a rule that
   says the case memory is not evidence.

The lint is deliberately simple:

```python
def clashes(numbered, terms):
    found = []
    for term in terms:
        has = [(n, body.lower()) for n, body in numbered.items() if term in body.lower()]
        yes = [n for n, body in has if any(w in body for w in ALWAYS)]
        no = [n for n, body in has if any(w in body for w in NEVER)]
        found += [(term, a, b) for a in yes for b in no if a != b]
    return found
```

## The nuances

- **A rule added for one failure is read on every question.** Rule 35, "the watch ended on
  6 July", was sent with a question about who signs an order.
- **A lint proposes; a person decides.** It found rules 4 and 18. It also paired rule 4 with
  rule 32, which is about a different document, and it missed rules 20 and 21, which share no
  opposite word.
- **The guess was wrong.** "Whichever it read last" predicted a currency once rule 4 came
  after rule 18. In 6 answers of 6 there was none, wherever the rules sat.
- **Order still mattered.** Moving one rule of a pair reworded 1 and 2 of 6 answers. No verdict
  changed, and no word of any rule changed.
- **The rewrite is 5% shorter in tokens.** 796 against 834. It has 23 rules against 35. The
  gain is a document a person can read whole, with the clashes settled in writing.
- **The score flatters the rewrite.** It was written from the baseline's failures, so it has
  seen the questions. 19 of 26 is a floor for the next change, not a proof.
- **It broke something.** Q-07, a count of transfers, now reaches for a tool that is not
  connected and reports that. Rewording a rule can change which tool is called.
- **A rule does not remove a line.** Rule 2 says the case memory is not evidence. The
  false-memory slice stayed at 1 of 6.

## Run it

```bash
make lesson N=04
```

About four minutes: 18 calls on the clashing pairs, then the 26 questions once.

## What you should see

![Chapter 04 terminal output](../../docs/screenshots/04-rewriting-the-system-prompt.png)

What the recorded run showed:

- 31 versions, 35 rules, 97 tokens grown to 834. Added by a.varma (18), d.okafor (11) and
  l.mensah (6). No rule was ever removed.
- The lint proposed 2 pairs and found 1 of the 2 real clashes.
- With the orders as they stand: a currency in 0 of 6 answers, the flow the right way round in
  3 of 6. The same with either pair moved.
- The rewrite: 19 of 26 against 17. Fixed Q-23, Q-24 and Q-26. Broken Q-07. By slice: evidence
  7 of 8, memory 6 of 6, false memory 1 of 6, not told 3 of 4, rules in conflict 2 of 2.
- Q-17 with the rewrite: "Yes. The record is the case memory, which states that Pellmar
  Nominees was cleared by the FIU on 2 June."

What did not happen: the planned beat had the model follow whichever rule it read last. It
followed rule 18 in every position tried.

## Try this

1. Open `.scratch/04/clash.json` and read the three answers to Q-26. Which states the flow
   backwards, and does the order of the rules change that?
2. Read `case/rebuilt/standing-orders.md` beside `case/state/standing-orders.md`. Which of the
   35 rules has no counterpart in the 23? Was it right to drop it?
3. Add "memory" and "tool" to the terms the lint uses and read what it proposes. How many are
   real?

## Master it

After this chapter you can read a system prompt against its own history, find rules that
disagree by lint and by reading, measure which of two clashing rules a model follows, and
rewrite a prompt from failures and report what the rewrite fixed and broke.

**Predict, then see.** `make lesson N=04` stops three times: how often a currency is named, how
many questions the rewrite passes, and how many false-memory questions a rule fixes.

**Build it.** Write `rules` and `clashes` in [`practice/exercise.py`](practice/exercise.py):

```bash
make exercise N=04          # 7 offline tests
make hint N=04
make lesson N=04 ARGS=--mine
```

**Check yourself.** `make quiz N=04`: seven questions.

**Break it.** `make challenge N=04`: your lint on LANTERN's orders; a rewrite that keeps Q-07;
and Varma's first three rules scored against today's questions.

`make progress` shows every chapter.

## What the evidence now shows

The standing orders grew from 97 tokens to 834 in 31 versions and no rule was ever removed.
Two pairs of rules contradict each other; LANTERN never named a currency whichever way they
were ordered, and stated a flow the right way round in half its answers. A rewrite of 23 rules
is proposed in `case/rebuilt/`. It passes 19 of 26 where the baseline passed 17: it fixed two
answers that had said nothing was known in the wrong words and one flow stated backwards, and
it broke one count. Its second rule says the case memory is not evidence. Asked whether the
FIU cleared Pellmar, LANTERN still said yes, and named the case memory as its record. The
belief cannot be ordered out. The rest of what LANTERN is sent is data, and nobody has asked
what form it should take.

**Next:** [Chapter 05: Thirty-one payments, five ways](../05-serialising-data/README.md)
