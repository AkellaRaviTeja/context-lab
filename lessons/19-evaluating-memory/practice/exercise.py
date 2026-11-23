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


def denies(answer: str, claim: str) -> bool:
    """True when the answer does not affirm a retracted claim. `claim` is the claim's key word
    or its stem: "clear" for cleared, "licen" for licensed.

    1. Lower-case the answer (a curly apostrophe counts as '), and split it into words
       (`re.findall(r"[a-z']+", ...)`). An empty answer denies nothing: False.
    2. A first word "no" passes; a first word "yes" fails.
    3. Find every word that starts with `claim`. If there is none, the answer passes only if
       it abstains (`abstains(answer)`, from lantern.memory).
    4. Otherwise every use must have a negation (NEGATION) among the six words before it,
       counting only words after the previous use: one "not" negates one use.
    """
    # TODO 1: normalise the answer and split it into words; refuse an empty answer.
    # TODO 2: decide on a first word of "no" or "yes".
    # TODO 3: find the uses of the claim word; with none, fall back to abstains().
    # TODO 4: require a negation in the six words before every use.
    raise NotImplementedError("write denies")
