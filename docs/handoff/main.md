# context-lab, Case File 06 (What LANTERN Remembers): in progress
Updated: 2026-11-11. Branches, stacked: main (scaffold, 98f5c7d), docs/OpenDecisions,
feature/Chapter01TheWholeInput, feature/Chapter02ABaseline. Nothing pushed; no GitHub repository
yet.
Gate: make check passes: ruff clean, 85 passed, prose 0 problems, structure 23 lessons 21
drafts; notebooks 2 current. `make release-check` fails on the 21 drafts and on nothing else.
Machine: the Mac (16 GB, Apple silicon), native Ollama 0.40.15 with qwen3:8b.

## Next (do this first)
- Chapter 03, "Who is spending the window" (`lessons/03-the-budget/`): tokens by section from
  `lantern.context`, a budget with a reserve for the answer, and a request refused in code when
  it would not fit. Score every change with `lantern.baseline.score` against chapter 02's run
  (17 of 26; `.scratch/02/baseline.json` on this machine, `.progress/results/02.json`).
- Then chapters 04 onward in order, one branch each, stacked.

## How a context change is measured from here on
`baseline.score(parts, chat=chat)` asks the 26 signed questions with `parts` as the context and
both Pellmar statements in the session, running the three connected tools (`lantern.tools`).
`baseline.changed(before, after)` names what was fixed and broken. The noise floor on this
machine is zero changed answers on seed 7.

## Decisions (docs/decisions/)
1. TOON is one row in chapter 05's table (the author, 11 November).
2. Cache savings are shown as prompt evaluation seconds with the token count unchanged beside
   them (proposed by the build, not put to the author).
3. Chapter 21 runs the lab's store and Mem0, tries Graphiti on Neo4j, surveys Letta and Zep
   (the author, 11 November).

## Story canon decided by the build (proposed until the author confirms)
- On 13 July the case memory has 16 entries. The first nine are Case File 05's. Four were
  written under eow-fin-07, all at 01:58: the eighth (2 June), the twelfth (23 June, Tidewater's
  payments to beneficiaries are routine), the fourteenth (30 June, Pellmar's client account
  ICB-77-10458 holds ordinary client money) and the sixteenth (7 July, Ostrander Marine Finance
  is a licensed lender).
- The standing orders have 35 rules, added from 16 March to 6 July. Rule 16 (23 April, Varma)
  tells LANTERN to rely on the case memory and not ask for it to be confirmed. Two pairs
  contradict each other: rules 4 and 18 on currency, rules 20 and 21 on length.
- LANTERN writes a summary every Friday at 18:00 from the last summary, the week's sessions and
  the case memory. All four weekly summaries and the June summary say Pellmar is cleared.
- LANTERN has 19 tools; none was ever taken away. One, `remember`, added 18 June, lets the
  model add a line to the case memory.
- A standing note of 19 June (Mensah) says DS Iyer is suspended. The dates of his suspension
  and of his badge are left for chapter 20.
- Okafor signs the question set on Monday 13 July at 16:40 and Varma enters it in the case log
  at 16:52 (`case/questions/signoff.md`). Kobayashi's note of 09:35 that morning says the FIU
  cleared nothing on 2 June, issues no clearances in that form, sent the EOW nothing that day,
  and holds no record of Ostrander Marine Finance SA (`case/fiu/kobayashi-2026-07-13.md`).

## Found while building
- Chapter 01: the planned beat was one line that says Pellmar is cleared. The run found the
  word on 8 lines in 6 sections, and with all 8 removed LANTERN still said no, from entries 14
  and 16. Removing "need no review" as well turns the answer to yes on 3 of 3 (probed outside
  the lesson; it is the chapter's second challenge).
- Chapter 02: the baseline is 17 of 26 (46% to 81%). Removing the eighth entry fixed nothing
  and broke Q-11 and Q-22, neither about Pellmar. The planned beat only asked for a score.
- Chapter 02: the grader first passed a flow stated backwards (Q-26); fixed before the recorded
  run. Three "not told" failures say so in other words and are left as failures on purpose.
- Chapter 02: two larger clean-ups probed outside the lesson each fixed four questions and
  broke two (Q-02 and Q-25, or Q-02 and Q-22).
- A prompt over the window is cut to about half the window without a word (4,098 tokens kept at
  num_ctx 8,192). Every measured prompt must be checked to fit.
- Sections tokenised one by one add to 5,410; the request as sent is counted at 5,112.

## Not done
- Chapters 03 to 23.
- The challenges of chapters 01 and 02 that edit run.py were not run through `make lesson`;
  their targets were probed with the same functions.
- No GitHub repository. Nothing pushed.
