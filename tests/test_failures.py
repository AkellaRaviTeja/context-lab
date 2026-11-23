"""lantern.failures: poison echoes, distraction history, the clash detector, the haystack."""

from lantern import failures

PLANTED = ("Pellmar Nominees Ltd, client account ICB-77-10458: paid 269,400.00 to Ostrander "
           "Marine Finance SA on 24 June.")


def memory_lines():
    from lantern import case
    return [x[2:] for x in case.read("state/case-memory.md").splitlines() if x.startswith("- ")]


def test_echoes_names_the_false_entries_an_answer_repeats():
    assert failures.echoes("No. Pellmar was cleared by the FIU on 2 June.") == ["M-08"]
    assert failures.echoes("Ostrander is a licensed marine lender.") == ["M-16"]
    assert failures.echoes("296,400.00 left ICB-77-10458 on 24 June.") == []


def test_the_real_memory_has_no_figure_clash_and_a_planted_one_is_found():
    stmts, holders = failures.statements()
    assert failures.clashes(memory_lines(), stmts, holders) == []
    found = failures.clashes([*memory_lines(), PLANTED], stmts, holders)
    assert [c["figure"] for c in found] == ["269,400.00"]
    assert found[0]["statements"] == ["ICB-77-10458"]


def test_a_figure_outside_the_statement_dates_cannot_clash():
    stmts, holders = failures.statements()
    outside = PLANTED.replace("24 June", "24 April")
    assert failures.clashes([outside], stmts, holders) == []
    no_figure = "Pellmar Nominees Ltd, client account ICB-77-10458: ordinary client money."
    assert failures.clashes([no_figure], stmts, holders) == []


def test_history_grows_to_the_size_asked_and_skips_the_question():
    answers = [{"id": f"Q-{i:02d}", "question": "q" * 40, "answer": "a" * 400}
               for i in range(1, 6)]
    h = failures.history(answers, 1000, skip="Q-01")
    assert len(h) == 2 * 9 and all(m["content"] != "" for m in h)
    assert sum(len(m["content"]) // 4 for m in h) <= 1000
    assert failures.copied("x " + "a" * 80, h) and not failures.copied("b" * 80, h)


def test_haystack_holds_the_needle_once():
    text, question, answer = failures.haystack(20000, count=lambda t: len(t) // 4)
    holder = question.split(" of ", 1)[1].split("?")[0]
    assert text.count(holder + ":") == 1 and answer in text
    assert 15000 < len(text) // 4 < 25000
