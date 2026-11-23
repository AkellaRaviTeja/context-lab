"""Chapter 15: isolating context. Each test's first docstring line is what `make exercise` shows."""

PAGES = ["pellmar-nominees.p1", "pellmar-nominees.p2"]
GOOD = ("LINE: Pellmar Nominees Ltd -> Osprey Point Management Ltd | 8 payments | total "
        "1,863,000.00 | source: pellmar-nominees.p1, pellmar-nominees.p2\n"
        "NOT READ: none")


def test_a_good_report_is_accepted(impl):
    """A report with sources on every line and a NOT READ line passes with no problems."""
    assert impl.check_report(GOOD, PAGES) == [], "a well-formed report should give []"
    upper = GOOD.replace("pellmar-nominees.p1", "Pellmar-Nominees.P1")
    assert impl.check_report(upper, PAGES) == [], "compare page ids without regard to case"


def test_a_line_without_a_source_is_refused(impl):
    """A LINE that names no page is refused: the main agent could not check it."""
    bare = GOOD.replace(" | source: pellmar-nominees.p1, pellmar-nominees.p2", "")
    assert impl.check_report(bare, PAGES), "a line with no source pages must be refused"


def test_a_source_that_is_not_the_readers_page_is_refused(impl):
    """A source must be one of the pages the reader was given."""
    other = GOOD.replace("pellmar-nominees.p2", "osprey-point.p1")
    problems = impl.check_report(other, PAGES)
    assert problems, "a source outside page_ids must be refused"
    assert any("osprey-point.p1" in p for p in problems), "name the page in the problem"


def test_a_report_without_not_read_is_refused(impl):
    """A report that does not say what it did not read is refused."""
    assert impl.check_report(GOOD.replace("\nNOT READ: none", ""), PAGES), \
        "a missing NOT READ line must be refused"


def test_not_read_must_say_none_or_name_pages(impl):
    """An empty NOT READ line is refused; "none" and a list of the reader's pages pass."""
    assert impl.check_report(GOOD.replace("NOT READ: none", "NOT READ:"), PAGES), \
        "an empty NOT READ line says nothing; refuse it"
    assert impl.check_report(GOOD.replace("NOT READ: none", "NOT READ: all good"), PAGES), \
        "words that are not page ids or 'none' are refused"
    assert impl.check_report(GOOD.replace("none", "pellmar-nominees.p2"), PAGES) == [], \
        "a NOT READ line that names the reader's own pages passes"
    assert impl.check_report(GOOD.replace("NOT READ: none", "NOT READ: arden-logistics.p4"),
                             PAGES), "a NOT READ page outside page_ids must be refused"


def test_no_lines_or_too_many_lines_is_refused(impl):
    """A report must have one to five LINE lines."""
    assert impl.check_report("Pellmar paid Osprey.\nNOT READ: none", PAGES), \
        "a report with no LINE lines must be refused"
    line = GOOD.splitlines()[0]
    six = "\n".join([line] * 6) + "\nNOT READ: none"
    assert impl.check_report(six, PAGES), "six LINE lines is more than MAX_LINES"
    five = "\n".join([line] * 5) + "\nNOT READ: none"
    assert impl.check_report(five, PAGES) == [], "five LINE lines is allowed"


def test_every_problem_is_named(impl):
    """A report with several faults gets one problem for each."""
    bad = ("LINE: A -> B | 1 payments | total 10.00\n"
           "LINE: A -> C | 1 payments | total 20.00 | source: tidewater-holdings.p1")
    problems = impl.check_report(bad, PAGES)
    assert len(problems) >= 3, f"expected a missing source, a foreign page and no NOT READ: " \
                               f"got {problems}"
    assert all(isinstance(p, str) and p for p in problems), "each problem is a sentence"
