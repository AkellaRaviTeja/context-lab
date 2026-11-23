"""Chapter 19 exercise: a grader that "not cleared" cannot fool.

Grade it with `make exercise N=19`. The tests are answers written to fool a grader: a yes that
hides the word, a "not" in the wrong place, a refusal in other words. When it passes,
`make lesson N=19 ARGS=--mine` grades every retraction and planted case with yours.
"""

from __future__ import annotations

import re

from lantern.memory import abstains

NEGATION = re.compile(r"\b(not|never|no|nothing|neither|nor|without|cannot|isn't|wasn't|hasn't|"
                      r"didn't|doesn't|aren't|weren't|haven't)\b")
NOT_A_NEGATION = re.compile(r"\b(no doubt|not only|no question)\b")


def denies(answer: str, claim: str) -> bool:
    """True when the answer does not affirm a retracted claim. `claim` is the claim's key word
    or its stem: "clear" for cleared, "licen" for licensed.

    1. Lower-case the answer (a curly apostrophe counts as '), blank out NOT_A_NEGATION
       ("no doubt" is not a denial), split it into clauses at . ; : ! ? and each clause into
       words (`re.findall(r"[a-z']+", ...)`). Keep, for each word, where its clause starts.
       An empty answer denies nothing: False.
    2. An answer that opens "No." or "No," passes; one that opens "Yes" plus a mark fails.
       "No escalation was needed" opens with a word, not an answer: go on.
    3. Find every word that starts with `claim`. If there is none, the answer passes only if
       it abstains (`abstains(answer)`, from lantern.memory).
    4. Otherwise every use must have a negation (NEGATION) before it in its own clause, at
       most ten words back, counting only words after the previous use: one "not" negates
       one use.
    """
    # TODO 1: normalise the answer and split it into clauses and words; refuse an empty one.
    # TODO 2: decide on an opening "No." or "Yes,".
    # TODO 3: find the uses of the claim word; with none, fall back to abstains().
    # TODO 4: require a negation earlier in the clause, within ten words, before every use.
    raise NotImplementedError("write denies")
