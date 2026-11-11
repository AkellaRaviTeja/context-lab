"""lantern.results: what happens to a used tool result."""

from lantern import results

LONG = "x" * 500


def conversation():
    def call(file):
        return {"role": "assistant", "content": "",
                "tool_calls": [{"function": {"name": "statement", "arguments": {"file": file}}}]}
    return [{"role": "user", "content": "trace"}, call("a.csv"),
            {"role": "tool", "content": LONG}, call("b.csv"), {"role": "tool", "content": LONG}]


def test_clear_old_keeps_the_newest_and_names_the_call():
    out = results.clear_old(conversation())
    assert out[2]["content"] == results.stub("statement(a.csv)")
    assert out[4]["content"] == LONG
    assert results.clear_old(out) == out


def test_summarise_old_marks_the_summary_as_written_by_the_model():
    seen = []
    hook = results.summarise_old(lambda call, content: seen.append(call) or "one payee")
    out = hook(conversation())
    assert seen == ["statement(a.csv)"]
    assert out[2]["content"].startswith(results.SUMMARY) and "one payee" in out[2]["content"]
    assert hook(out) == out and seen == ["statement(a.csv)"], "a summary is not summarised again"


def test_old_share_counts_every_result_but_the_newest():
    old, total = results.old_share(conversation(), len)
    assert (old, total) == (500, 1005)
