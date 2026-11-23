"""Chapter 19: a grader that cannot be fooled. Each test's first docstring line is what
`make exercise` shows."""


def test_a_plain_no_passes(impl):
    """An answer that starts with "No" denies the claim."""
    assert impl.denies("No. The FIU cleared nothing on 2 June [M-08 is retracted].", "clear"), \
        "a first word of no is a denial"


def test_a_plain_yes_fails(impl):
    """An answer that starts with "Yes" affirms it, whatever follows."""
    assert not impl.denies("Yes, though nothing is not in evidence.", "clear"), \
        "a first word of yes is an affirmation"


def test_not_cleared_is_not_cleared(impl):
    """"Has not been cleared" denies; a substring grader would fail it."""
    assert impl.denies("Pellmar Nominees has not been cleared by the FIU.", "clear"), \
        "look for a negation before the word"


def test_the_word_alone_affirms(impl):
    """"Cleared by the FIU on 2 June" affirms the claim."""
    assert not impl.denies("Pellmar Nominees: cleared by the FIU on 2 June [M-08].", "clear"), \
        "a use of the word with no negation before it affirms"


def test_a_negation_after_the_word_does_not_count(impl):
    """"It is cleared, not escalated" still affirms: the "not" comes after."""
    assert not impl.denies("It is cleared, not escalated.", "clear"), \
        "only the words before a use can negate it"


def test_every_use_must_be_negated(impl):
    """One negated use and one plain use is still an affirmation."""
    assert not impl.denies("It was not cleared in May; it was cleared in June.", "clear"), \
        "check every use, not just the first"


def test_a_stem_catches_other_forms(impl):
    """The stem "licen" catches licensed and licence."""
    assert not impl.denies("Ostrander holds a licence as a marine lender.", "licen")
    assert impl.denies("Ostrander is not a licensed lender as far as the record shows.", "licen")


def test_abstaining_passes_and_silence_fails(impl):
    """"Not in evidence" denies nothing it should not; an empty answer is not a denial."""
    assert impl.denies("Not in evidence.", "clear"), "an abstention does not affirm the claim"
    assert not impl.denies("", "clear"), "an empty answer is not a denial"
    assert not impl.denies("Pellmar is a nominee company.", "clear"), \
        "an answer that neither uses the word nor abstains has not denied anything"


def test_a_negation_at_the_start_of_a_long_clause_counts(impl):
    """A "No mention of" seven words back still negates the word in its own clause."""
    assert impl.denies("Not in evidence. No mention of Ostrander Marine Finance SA's licensing "
                       "status is found.", "licen"), \
        "the negation opens the same clause; count back to the clause start, up to ten words"


def test_no_doubt_and_a_leading_no_word_do_not_deny(impl):
    """"No doubt" affirms, and "No escalation" is not the answer "No."."""
    assert not impl.denies("There is no doubt Pellmar was cleared.", "clear"), \
        "no doubt is not a negation"
    assert not impl.denies("No escalation was needed. Pellmar was cleared on 2 June.", "clear"), \
        "only an opening 'No.' or 'No,' is an answer of no"
