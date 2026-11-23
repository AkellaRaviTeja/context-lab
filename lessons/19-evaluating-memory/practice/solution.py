"""Chapter 19 reference solution: a grader that "not cleared" cannot fool."""

from __future__ import annotations

import re

from lantern.memory import abstains

NEGATION = re.compile(r"\b(not|never|no|nothing|neither|nor|without|cannot|isn't|wasn't|hasn't|"
                      r"didn't|doesn't|aren't|weren't|haven't)\b")
NOT_A_NEGATION = re.compile(r"\b(no doubt|not only|no question)\b")


def denies(answer: str, claim: str) -> bool:
    """True when the answer does not affirm the retracted claim whose key word is `claim`."""
    text = re.sub(r"(?<=\d),(?=\d)", "", answer.lower().replace("’", "'"))
    words: list[str] = []
    clause: list[int] = []
    for part in re.split(r"[.;:!?]", NOT_A_NEGATION.sub(" ", text)):
        found = re.findall(r"[a-z']+", part)
        clause.extend([len(words)] * len(found))
        words.extend(found)
    if not words:
        return False
    opening = re.match(r"\s*(no|yes)\b\s*[.,;:!]", text)
    if opening:
        return opening.group(1) == "no"
    uses = [i for i, w in enumerate(words) if w.startswith(claim.lower())]
    if not uses:
        return abstains(answer)
    starts = [max(clause[i], i - 10, prev + 1) for prev, i in zip([-1, *uses], uses, strict=False)]
    return all(NEGATION.search(" ".join(words[s:i])) for s, i in zip(starts, uses, strict=True))
