"""lantern.tracing: one span per model call and per tool, with GenAI attributes."""

import json

from lantern import agent, llm, tracing
from lantern.llm import Reply, ToolCall


def test_a_traced_agent_run_writes_agent_chat_and_tool_spans(tmp_path, monkeypatch):
    replies = iter([Reply("", "qwen3:8b", tool_calls=[ToolCall("look", {"q": "x"})],
                          prompt_tokens=120, output_tokens=9, latency=0.5, cost=0.0),
                    Reply("done", "qwen3:8b", prompt_tokens=150, output_tokens=3, cost=0.0)])
    monkeypatch.setattr(llm, "_ollama", lambda *a, **k: next(replies))
    monkeypatch.setattr(agent, "weigh", lambda m, s=None: {"user": 10})
    path = tmp_path / "t.jsonl"
    tracing.enable(path)
    try:
        run = agent.run([{"role": "user", "content": "go"}], chat=llm.chat, schemas=[],
                        handlers={"look": lambda q: "seen"})
    finally:
        tracing._provider = None
    assert run.answer == "done"
    spans = [json.loads(line) for line in path.read_text().splitlines()]
    ops = [s["attributes"]["gen_ai.operation.name"] for s in spans]
    assert ops == ["chat", "execute_tool", "chat", "invoke_agent"]
    chat = spans[0]["attributes"]
    assert chat["gen_ai.usage.input_tokens"] == 120 and chat["gen_ai.provider.name"] == "ollama"
    assert spans[1]["attributes"]["gen_ai.tool.name"] == "look"
    root = spans[-1]
    assert all(s["trace_id"] == root["trace_id"] for s in spans), "one trace for the run"
    assert spans[0]["parent_id"] == root["span_id"]


def test_tracing_is_off_unless_asked(monkeypatch):
    monkeypatch.delenv("LANTERN_TRACE", raising=False)
    tracing._provider = None
    with tracing.span("x") as s:
        assert s is None
