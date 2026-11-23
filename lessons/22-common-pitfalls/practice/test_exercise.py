"""Chapter 22: a held-out split and the propose, score, keep loop. Each test's first docstring
line is what `make exercise` shows."""

from lantern import baseline, case, optimise
from lantern.testing import Scripted, say

QUESTIONS = baseline.questions()
START = case.read("state/standing-orders.md")


def orders(n):
    """A standing-orders text with n numbered rules."""
    return "# Orders\n" + "".join(f"{i}. Rule {i}.\n" for i in range(1, n + 1))


def scorer(table):
    """A scorer that passes as many of four questions as `table` says for each text."""
    table = {k.strip(): v for k, v in table.items()}

    def score(text):
        k = table[text.strip()]
        return [{"id": f"Q-{i}", "question": f"q{i}", "answer": "a", "passed": i <= k}
                for i in range(1, 5)]
    return score


def test_split_takes_every_slice_and_shares_nothing(impl):
    """Two of every slice for training and two more held out, with no id in both."""
    train, held = impl.split(QUESTIONS, train=2, held=2, seed=22)
    assert not set(train) & set(held), "no question may be in both splits"
    slices = {q["id"]: q["slice"] for q in QUESTIONS}
    for s in set(slices.values()):
        assert sum(slices[i] == s for i in train) == 2, f"two {s} questions for training"
    assert len(held) == 8, f"the two-question slice has none left to hold out: {held}"


def test_split_is_the_same_for_the_same_seed(impl):
    """The same seed gives the same split; another seed gives another."""
    a = impl.split(QUESTIONS, train=2, held=2, seed=22)
    assert a == impl.split(QUESTIONS, train=2, held=2, seed=22), "seed the shuffle"
    assert a != impl.split(QUESTIONS, train=2, held=2, seed=5), "shuffle with the seed given"


def test_split_matches_the_lesson(impl):
    """With the lesson's settings, the same split as lantern.optimise."""
    assert impl.split(QUESTIONS, train=2, held=2, seed=22) == \
        optimise.split(QUESTIONS, train=2, held=2, seed=22), \
        "shuffle each slice with one Random(seed), slices in the order they first appear"


def test_a_better_revision_is_kept(impl):
    """A revision that passes more training questions becomes the best."""
    a, b = orders(6), orders(7)
    h = impl.optimise(a, propose=lambda o, f: b, score=scorer({a: 1, b: 3}), rounds=1)
    assert [x["kept"] for x in h] == [True, True] and h[1]["passed"] == 3, h


def test_a_tie_or_worse_is_dropped(impl):
    """Keep only what passes strictly more than the best so far."""
    a, b, c = orders(6), orders(7), orders(8)
    props = iter([b, c])
    h = impl.optimise(a, propose=lambda o, f: next(props), score=scorer({a: 2, b: 2, c: 1}),
                      rounds=2)
    assert [x["kept"] for x in h] == [True, False, False], [x.get("why") for x in h]
    assert h[1]["why"].startswith("dropped"), h[1]["why"]


def test_the_proposer_starts_from_the_best_and_its_failures(impl):
    """Each round proposes from the best orders so far and the questions they failed."""
    a, b, c = orders(6), orders(7), orders(8)
    seen = []

    def propose(o, failed):
        seen.append((o, [r["id"] for r in failed]))
        return b if len(seen) == 1 else c

    impl.optimise(a, propose=propose, score=scorer({a: 1, b: 3, c: 2}), rounds=2)
    assert seen == [(a, ["Q-2", "Q-3", "Q-4"]), (b, ["Q-4"])], seen


def test_malformed_and_unchanged_revisions_are_not_scored(impl):
    """A reply with too few rules, or the same text again, costs no scoring."""
    a = orders(6)
    calls = []

    def score(text):
        calls.append(text)
        return scorer({a: 1})(text)

    props = iter(["I cannot help with that.", a + "\n"])
    h = impl.optimise(a, propose=lambda o, f: next(props), score=score, rounds=2)
    assert len(calls) == 1, "only round 0 is scored"
    assert all(x["passed"] is None and x["why"].startswith("not scored") for x in h[1:]), h


def test_start_results_are_used_and_not_asked_again(impl):
    """Given round 0's results, the loop does not score the start again."""
    a, b = orders(6), orders(7)
    given = [{"id": "Q-1", "question": "q", "answer": "a", "passed": True}]
    h = impl.optimise(a, propose=lambda o, f: b, score=scorer({b: 1}), rounds=1,
                      start_results=given)
    assert h[0]["results"] is given and h[0]["passed"] == 1 and not h[1]["kept"], h


def test_the_model_proposes_from_the_training_failures_only(impl):
    """With a scripted model as the proposer, its prompt holds training failures only."""
    model = Scripted([say(START.replace("Keep every answer short.", "Be brief."))])
    train = [{"id": "Q-21", "question": "Who are the directors of Ostrander Marine Finance SA?",
              "answer": "John Smith.", "passed": False}]
    qmap = {q["id"]: q for q in QUESTIONS}

    def propose(o, failed):
        return optimise.propose(o, optimise.failures(failed, qmap), chat=model)

    h = impl.optimise(START, propose=propose, score=lambda o: train, rounds=1,
                      start_results=train)
    prompt = model.requests[0]["messages"][0]["content"]
    assert "Ostrander Marine Finance SA" in prompt and "Saltire Quay" not in prompt, \
        "the proposer is shown the failures it is given, and nothing held out"
    assert h[1]["passed"] == 0 and not h[1]["kept"]


def test_a_copy_with_a_new_title_and_spaces_is_not_scored(impl):
    """The first live run scored the same rules three times: title gone, spaces added."""
    a = "# Standing orders\n" + orders(6).split("\n", 1)[1]
    copy = a.split("\n", 1)[1].replace(". ", ".  ") + "  \n"
    calls = []

    def score(text):
        calls.append(text)
        return scorer({a: 1})(text)

    h = impl.optimise(a, propose=lambda o, f: copy, score=score, rounds=2)
    assert len(calls) == 1, "a copy is not a revision: only round 0 is scored"
    assert all("not scored" in x["why"] for x in h[1:]), [x["why"] for x in h]
