import json

import httpx
import pytest

from lantern import load_config, stream


class FakeStream:
    """Stands in for httpx.stream(...): a context manager whose response yields JSON lines."""

    def __init__(self, lines, seen):
        self.lines, self.seen = lines, seen
        self.status_code = 200

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.seen["closed"] = True

    def raise_for_status(self):
        pass

    def iter_lines(self):
        for line in self.lines:
            self.seen["read"] = self.seen.get("read", 0) + 1
            yield line


@pytest.fixture
def fake(monkeypatch):
    seen = {}
    lines = [
        json.dumps({"message": {"role": "assistant", "content": "Arden "}, "done": False}),
        "",
        json.dumps({"message": {"role": "assistant", "content": "Logistics"}, "done": False}),
        json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {"function": {"name": "sum_payments", "arguments": {"payer": "Halcyon"}}}
                    ],
                },
                "done": False,
            }
        ),
        json.dumps(
            {
                "message": {"role": "assistant", "content": ""},
                "done": True,
                "prompt_eval_count": 40,
                "eval_count": 3,
            }
        ),
    ]

    def fake_stream(method, url, json, timeout):
        seen.update(method=method, url=url, body=json, timeout=timeout)
        return FakeStream(lines, seen)

    monkeypatch.setattr(httpx, "stream", fake_stream)
    return seen


def test_stream_sends_stream_true_and_config_defaults(fake):
    list(stream("Who?", tools=[{"type": "function", "function": {"name": "x"}}]))
    body = fake["body"]
    assert fake["method"] == "POST" and fake["url"].endswith("/api/chat")
    assert body["stream"] is True
    assert body["tools"][0]["function"]["name"] == "x"
    assert body["options"]["num_predict"] == load_config()["generation"]["max_tokens"]
    assert fake["timeout"] == load_config()["limits"]["request_timeout_s"]


def test_stream_yields_text_tool_calls_and_final_counts(fake):
    chunks = list(stream("Who?"))
    assert "".join(c.text for c in chunks) == "Arden Logistics"
    calls = [c for c in chunks if c.tool_calls]
    assert calls[0].tool_calls[0].name == "sum_payments"
    assert calls[0].tool_calls[0].arguments == {"payer": "Halcyon"}
    assert chunks[-1].done and chunks[-1].output_tokens == 3 and chunks[-1].prompt_tokens == 40


def test_stopping_early_closes_the_connection(fake):
    for chunk in stream("Who?"):
        if chunk.text:
            break
    assert fake["closed"] is True and fake["read"] == 1
