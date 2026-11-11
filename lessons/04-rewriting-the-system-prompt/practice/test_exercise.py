"""Chapter 04: standing orders. Each test's first docstring line is what `make exercise` shows."""

ORDERS = """# Standing orders

Some unnumbered text. 3 things matter.

1. Always give amounts with their currency.
2. Cite the evidence.
3. Never state a Currency. The statements give none.
4. Every answer is short. Do not pad an answer.
10. Write dates in full.
"""


def test_rules_are_the_numbered_lines(impl):
    """Headings, blank lines and unnumbered text are not rules."""
    r = impl.rules(ORDERS)
    assert sorted(r) == [1, 2, 3, 4, 10]
    assert r[2] == "Cite the evidence."
    assert r[10] == "Write dates in full."


def test_a_rule_keeps_its_whole_line(impl):
    """A rule with two sentences is one rule."""
    assert impl.rules(ORDERS)[3] == "Never state a Currency. The statements give none."


def test_a_clash_is_found_whatever_the_case(impl):
    """"Currency" and "currency" are the same term."""
    assert impl.clashes(impl.rules(ORDERS), ["currency"]) == [("currency", 1, 3)]


def test_no_shared_term_no_clash(impl):
    """Rules that pull opposite ways are only paired when they share the term."""
    assert impl.clashes(impl.rules(ORDERS), ["evidence", "dates"]) == []


def test_a_rule_is_not_paired_with_itself(impl):
    """One rule that both demands and forbids is not a pair."""
    assert impl.clashes(impl.rules(ORDERS), ["answer"]) == []


def test_terms_come_back_in_the_order_given(impl):
    """Every pair names its term, in the order the terms were given."""
    numbered = {1: "Always cite a tool.", 2: "Never call a tool twice.",
                3: "Every amount has a currency.", 4: "Do not state a currency."}
    assert impl.clashes(numbered, ["tool", "currency"]) == [("tool", 1, 2), ("currency", 3, 4)]


def test_on_the_real_orders_the_lint_finds_one_clash_and_one_false_alarm(impl):
    """On LANTERN's 35 rules: 4 against 18, and 4 against 32, which is no clash at all."""
    from lantern import case

    numbered = impl.rules(case.read("state/standing-orders.md"))
    assert len(numbered) == 35
    assert impl.clashes(numbered, ["currency"]) == [("currency", 4, 18), ("currency", 4, 32)]
