"""Chapter 07: the cut-off. Each test's first docstring line is what `make exercise` shows."""


def pages(impl):
    return [
        impl.Page("a.md", "Hold notice", "The hold on MTB-31-02290 under MTB-ORD-0001 began at "
                                         "11:30. Balance held: 2,284,893.10."),
        impl.Page("b.md", "Fee note", "Pellmar Nominees Ltd fee note to Corvane Trading Ltd: "
                                      "1,183.37."),
        impl.Page("c.md", "Telephone bill", "Line rental for 14 lines: 1,120.00."),
    ]


def test_overlap_is_a_share_of_the_question(impl):
    """Overlap is what share of the question's terms the page holds, not how long the page is."""
    p = impl.Page("x.md", "t", "reserve held order")
    assert impl.overlap("reserve held", p) == 1.0
    assert impl.overlap("reserve held order court", p) == 0.75
    assert impl.overlap("telephone", p) == 0.0


def test_common_words_do_not_count(impl):
    """A page does not match because it says "Pellmar" or "the" like the question does."""
    p = impl.Page("x.md", "t", "Pellmar Nominees Ltd account for the quarter")
    assert impl.overlap("Which account of Pellmar Nominees Ltd was held?", p) == 0.0


def test_a_question_with_nothing_telling_scores_zero(impl):
    """A question made only of common words scores 0.0 and does not divide by zero."""
    p = impl.Page("x.md", "t", "anything at all")
    assert impl.overlap("What is it?", p) == 0.0


def test_figures_match_with_or_without_commas(impl):
    """2,284,893.10 on the page matches 2284893.10 in the question."""
    assert impl.overlap("2284893.10", pages(impl)[0]) == 1.0


def test_select_admits_at_the_threshold(impl):
    """A page whose score equals the threshold is admitted."""
    kept, left = impl.select(pages(impl), "How much is held under MTB-ORD-0001?", 1.0)
    assert [p.path for p in kept] == ["a.md"]
    assert [path for path, _ in left] == ["b.md", "c.md"]


def test_everything_left_out_is_recorded_with_its_score(impl):
    """Every page is in one list or the other, and a page left out carries its score."""
    kept, left = impl.select(pages(impl), "What did Corvane Trading pay in fees?", 0.9)
    assert kept == []
    assert left == [("a.md", 0.0), ("b.md", 0.5), ("c.md", 0.0)]


def test_a_threshold_of_zero_admits_everything(impl):
    """With no cut-off every page is admitted, in the order it came."""
    kept, left = impl.select(pages(impl), "anything", 0.0)
    assert [p.path for p in kept] == ["a.md", "b.md", "c.md"] and left == []
