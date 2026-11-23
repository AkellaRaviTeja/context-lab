# 0004: Amendment A1 is placed in chapter 22, not as a new chapter 05

Status: Proposed, 21 November 2026. A choice of placement made by the build; the author has
not been asked and may change it.

## Context

Amendment A1 in `docs/roadmap/gaps.md` adds a chapter, "Letting a program rewrite it", after
chapter 04: an optimiser proposes variants of the standing orders and keeps the ones that score
better, shown beside the hand-written rewrite on a held-out set. The amendment takes the lab
from 23 chapters to 24.

When the quality-bar work opened this lab on 21 November 2026, chapters 05 to 09 were built and
committed, with recorded runs, screenshots, notebooks, practice folders and story beats in the
series bible that cite them by number. Inserting a chapter 05 renumbers nineteen folders, their
screenshots, their recorded results under `.progress/`, every "Next" link and every chapter
number in the bible.

## Decision

A1 is taught inside chapter 22, "Common pitfalls", as the pitfall "a context tuned without a
baseline", which is already on Varma's list for that chapter. The loop of propose, score and
keep is written in the lesson; the optimiser runs on a training split of the signed questions
and is scored on a held-out split; the chapter shows what it learned that holds only on the
cases it saw, and whether its best prompt drops "not in evidence". The library comparison the
amendment names (DSPy) belongs to the frameworks review and is listed there as not run unless
chapter 21 runs it.

## Consequences

- The lab keeps 23 chapters and every chapter keeps its number.
- A1's "by hand first" requirement is met in chapter 22; its placement after chapter 04 is
  not. If the author wants it after 04, the cost is the renumbering above.
