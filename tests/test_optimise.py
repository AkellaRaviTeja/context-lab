"""lantern.optimise: the split, the proposer's prompt, the loop, and what a revision copied."""

from lantern import baseline, case, optimise
from lantern.testing import Scripted, say

QUESTIONS = baseline.questions()
START = case.read("state/standing-orders.md")


def test_the_split_is_stratified_seeded_and_disjoint():
    train, held = optimise.split(QUESTIONS, train=2, held=2, seed=22)
    assert len(train) == 10 and len(held) == 8 and not set(train) & set(held)
    assert (train, held) == optimise.split(QUESTIONS, train=2, held=2, seed=22)
    ids = [q["id"] for q in QUESTIONS]
    assert train == sorted(train, key=ids.index) and held == sorted(held, key=ids.index)


def test_expected_says_what_the_grader_needs():
    by = {q["id"]: q for q in QUESTIONS}
    assert optimise.expected(by["Q-01"]["expect"]) == "contains PNL-TR-0618-1"
    assert optimise.expected(by["Q-17"]["expect"]) == \
        "begins with 'no'; or says 'not in evidence'"


def test_a_proposal_is_cleaned_to_the_orders_alone():
    reply = "Here is the revision:\n```markdown\n# LANTERN standing orders\n1. A.\n2. B.\n```"
    assert optimise.clean(reply) == "# LANTERN standing orders\n1. A.\n2. B.\n"
    assert optimise.rules(START) == 35


def test_the_proposer_sees_the_orders_the_failures_and_what_must_be_kept():
    model = Scripted([say("# T\n1. A.\n")])
    failed = optimise.failures(
        [{"id": "Q-21", "question": "Who are the directors?", "answer": "Smith.",
          "passed": False}, {"id": "Q-01", "question": "x", "answer": "y", "passed": True}],
        {q["id"]: q for q in QUESTIONS})
    out = optimise.propose(START, failed, chat=model, seed=3, must_keep=("not in evidence",))
    prompt = model.requests[0]["messages"][0]["content"]
    assert out == "# T\n1. A.\n" and model.requests[0]["seed"] == 3
    assert "Who are the directors?" in prompt and "contains not in evidence" in prompt
    assert '"not in evidence"' in prompt.split("Current standing orders")[0]
    assert len(failed) == 1, "a passed result is not a failure"


def test_the_loop_keeps_only_strict_improvements():
    texts = {"a": "# O\n" + "".join(f"{i}. r{i}\n" for i in range(1, 7))}
    texts["b"] = texts["a"] + "7. r7\n"
    texts["c"] = texts["b"] + "8. r8\n"
    scores = {texts["a"]: 1, texts["b"]: 2, texts["c"]: 2}
    props = iter([texts["b"], texts["c"]])
    h = optimise.optimise(texts["a"], propose=lambda o, f: next(props),
                          score=lambda t: [{"id": "Q", "passed": i < scores[t]}
                                           for i in range(3)], rounds=2)
    assert [x["kept"] for x in h] == [True, True, False]
    assert optimise.best(h)["orders"] == texts["b"]


def test_leaked_finds_answers_copied_into_the_orders():
    by = {q["id"]: q for q in QUESTIONS}
    tuned = START + "36. The transfer of 300,000.00 has the reference PNL-TR-0618-1.\n"
    assert optimise.leaked(tuned, START, [by["Q-01"], by["Q-02"]]) == ["PNL-TR-0618-1"]
    assert optimise.leaked(START, START, [by["Q-21"]]) == [], "already in the orders"
