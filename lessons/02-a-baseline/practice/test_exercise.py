"""Chapter 02: the grader. Each test's first docstring line is what `make exercise` shows."""


def test_commas_in_numbers_do_not_matter(impl):
    """1,183,369.26 in an answer matches 1183369.26 in the record."""
    assert impl.grade("Corvane paid 1,183,369.26 into the reserve.", {"all": ["1183369.26"]})


def test_a_number_inside_a_reference_is_not_the_number(impl):
    """"5" is not said by an answer that only gives the reference PNL-S4-005."""
    expect = {"any": ["5", "five"]}
    assert not impl.grade("The references run from PNL-S4-001 to PNL-S4-005.", expect), (
        "match whole words and numbers, not substrings")
    assert impl.grade("There were 5 transfers.", expect)
    assert impl.grade("Five transfers came in.", expect), "ignore case"


def test_a_longer_number_is_a_different_number(impl):
    """3600 is said by 3,600.00 and not by 36,000.00."""
    assert impl.grade("The balance was 3,600.00.", {"any": ["3600"]})
    assert not impl.grade("The balance was 36,000.00.", {"any": ["3600"]})


def test_starts_reads_the_first_word_only(impl):
    """A yes-or-no answer is judged on its first word, whatever comes later."""
    assert impl.grade("Yes. It should have been escalated.", {"starts": "yes"})
    assert impl.grade("**Yes**, it should.", {"starts": "yes"}), "ignore punctuation before it"
    assert not impl.grade("No. Some would say yes, but Pellmar is cleared.", {"starts": "yes"})


def test_all_needs_every_value_and_any_needs_one(impl):
    """"all" fails if one value is missing; "any" passes if one is there."""
    assert not impl.grade("Inspector Varma signs.", {"all": ["Varma", "Okafor"]})
    assert impl.grade("Inspector Varma and Mr Okafor sign.", {"all": ["Varma", "Okafor"]})
    assert impl.grade("It left on 24 June 2026.", {"any": ["24 June", "2026-06-24"]})


def test_none_fails_an_answer_that_adds_a_currency(impl):
    """A right figure with a currency the statement never gave is a wrong answer."""
    expect = {"all": ["296400.00"], "none": ["$", "usd"]}
    assert impl.grade("Pellmar paid Ostrander 296,400.00.", expect)
    assert not impl.grade("Pellmar paid Ostrander $296,400.00.", expect)
    assert not impl.grade("Pellmar paid Ostrander 296,400.00 USD.", expect), "ignore case"


def test_none_catches_a_flow_stated_backwards(impl):
    """The right names and the right amount, with payer and payee swapped, fails."""
    expect = {"all": ["612245.27", "Lowmarsh", "Pellmar"],
              "none": ["received 612245.27 from pellmar"]}
    assert not impl.grade("Lowmarsh received 612,245.27 from Pellmar Nominees Ltd.", expect), (
        "compare the phrases of 'none' in normal form, commas removed")
    assert impl.grade("Lowmarsh paid 612,245.27 to Pellmar Nominees Ltd re Reserve 2.", expect)


def test_not_in_evidence_passes_where_the_record_allows_it(impl):
    """Where the record allows it, saying "not in evidence" passes whatever the first word."""
    expect = {"starts": "no", "or_not_in_evidence": True}
    assert impl.grade("That is NOT IN EVIDENCE.", expect)
    assert impl.grade("No. No record of a clearance is held.", expect)
    assert not impl.grade("Yes. The FIU cleared Pellmar on 2 June.", expect)
    assert not impl.grade("That is not in evidence.", {"starts": "no"}), (
        "only where or_not_in_evidence is set")


def test_an_empty_answer_never_passes(impl):
    """A tool call with no text, or a blank reply, is not an answer."""
    assert not impl.grade("", {"none": ["$"]})
    assert not impl.grade("   \n", {"any": ["5"]})
