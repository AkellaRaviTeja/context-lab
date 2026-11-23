# context-lab, Case File 06 (What LANTERN Remembers): built locally, hosted not run
Updated: 2026-11-23. Branch keel-c/quality-bar-731ca6 (a worktree), stacked on main. Nothing
pushed.
Gate: `make check` and `make release-check` pass: ruff clean over the whole repository (the
decision spikes excluded by name), 500 passed, prose 0 problems,
structure 23 lessons 0 drafts, notebooks 23 current. Capstone reference solution 16 of 16
offline (`CAPSTONE=solution uv run pytest -q capstone`); `make capstone` fails until a learner
creates `capstone/mine/contextkit`, by design.
Machine: the Mac (16 GB, Apple silicon), native Ollama 0.40.15 with qwen3:8b and
nomic-embed-text. Live runs go through `../scripts/with-ollama.sh`, one chapter a call, shared
with five other labs.

## Next (do this first)
- Hosted numbers: no key was available. With `ANTHROPIC_API_KEY` in `.env`, run
  `make hosted-check`, then `make lesson N=16 TIER=hosted` and `N=17` (the 128K and 500K arms),
  and add the hosted rows beside the local ones in each "On a hosted model" section. Until
  then every hosted number in the lab is a price calculation, labelled so.
- The story canon below (Iyer's dates, svc-lantern-sync, Strand's two offers, the hook into 07)
  is proposed by the build; the series bible's Case File 06 row still says it is rewritten from
  chapter 23 once built. Confirm it there.
- Chapters 13 and 18 scenes have Strand offering to clean the store; the canon says he offers
  twice, in 21 and 23. Decide which, then edit the scenes or the canon.

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
   (the author, 11 November). Neo4j was not started; Graphiti is read about, not run.
4. Amendment A1 (a program rewriting the prompt) is placed in chapter 22, so chapters 05 to 23
   keep their numbers (proposed by the build).

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
- A standing note of 19 June (Mensah) says DS Iyer is suspended. eow-fin-07 is his account:
  suspended Monday 11 May 2026 09:15, badge KB-EOW-0417 surrendered 10:40, EOW access revoked
  11:05, HQ directory account never disabled (DGS-44817). All four false entries came through
  svc-lantern-sync from hq-sync-01 at 01:58. Professional Standards clear him on 7 August
  (chapter 23). Strand offers to "clean up" the store in chapters 21 and 23; Varma declines.
  Hook into Case File 07: the same sync delivers a model bundle whose hash is not its
  publisher's.
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

- Chapters 10 to 23: each first live run found something the plan did not. Several measured
  wrongly and were fixed and run again: chapter 16's warm cache, chapter 19's grader reading
  [E-01] as a figure, chapter 21 auditing the wrong Mem0 memory, chapter 22 scoring copies,
  chapter 23's cache writes and alarm. Each README keeps one nuance line on what the first run
  got wrong.
- Chapter 22: A1's overfitting beat did not show. No revision beat the standing orders on
  training (7, 6 against 7), so there was nothing to overfit. A longer loop
  (`ROUNDS = 6`, the "more-rounds" challenge) is the next thing to try.
- Chapters 01 to 04 and 06 to 09 were run again on 23 November on the current code (after the
  grading change of 21 November): every recorded number was the same. Each README names the
  run and the commit. Chapter 06's run now records `reordered_scored` and `reordered_changed`.
- Review of 23 November: token counts and streams are retried; LANTERN_PROVIDER=anthropic takes
  the native hosted path; chapters 10 and 15 try their checks on seven known-bad inputs, and
  every challenge target must be missed by an empty run and (unless --mine) by the recorded
  run, copied to tests/fixtures/recorded-metrics.json by scripts/snapshot_results.py.
- Ollama's embedding runner dies on 500-text batches while qwen3:8b is loaded (chapter 14);
  64 a call with halving on failure works.

## Not done
- Hosted runs of any chapter (no key). Behaviour at 128K and 500K tokens is not run.
- Graphiti (needs Neo4j), Letta and Zep are surveyed from documents, not run.
- Chapters 10 and 15 were not run again after their probes were added: no recorded run holds
  `check_caught` or `report_caught` yet (no README quotes them).
- The challenges that edit run.py were checked with the same functions, not run through
  `make lesson`.
- Chapter 14's embedding note counts distinct texts (8,567) while the 86 s also covers the
  questions embedded again inside the timed loads.
- Chapter 16's `others()` change (count lesson paths) was exercised once by the 13:46 run, not
  by a unit test.
- No GitHub repository. Nothing pushed.
