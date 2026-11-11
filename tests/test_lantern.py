import httpx
import pytest

from lantern import case, chat, config, load_config, tool_result


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture
def captured(monkeypatch):
    seen = {}

    def fake_post(url, json, timeout):
        seen["url"], seen["body"] = url, json
        return FakeResponse(
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "sum_payments",
                                "arguments": {"vendor": "Northwind"},
                            }
                        },
                        {"function": {"name": "lookup_company", "arguments": '{"name": "Arden"}'}},
                    ],
                },
                "prompt_eval_count": 40,
                "eval_count": 10,
                "eval_duration": 2_000_000_000,
            }
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    return seen


SUM_TOOL = {
    "type": "function",
    "function": {
        "name": "sum_payments",
        "description": "Total of all payments to one vendor.",
        "parameters": {
            "type": "object",
            "properties": {"vendor": {"type": "string"}},
            "required": ["vendor"],
        },
    },
}


def test_config_has_models_and_limits():
    cfg = load_config()
    assert {"default", "small"} <= set(cfg["models"])
    assert cfg["limits"]["max_turns"] > 0


def test_evidence_never_defaults_to_cloud():
    cfg = load_config()
    assert cfg["provider"] == "ollama"
    assert cfg["synthetic"]["cloud"] is False


def test_alias_resolves_to_model_name():
    assert config.model_name("small") == load_config()["models"]["small"]
    assert config.model_name("some:other") == "some:other"


def test_chat_sends_tools_and_parses_calls(captured):
    r = chat("Total paid to Northwind?", system="Use tools.", tools=[SUM_TOOL])
    body = captured["body"]
    assert captured["url"].endswith("/api/chat")
    assert body["tools"] == [SUM_TOOL]
    assert [m["role"] for m in body["messages"]] == ["system", "user"]
    assert [c.name for c in r.tool_calls] == ["sum_payments", "lookup_company"]
    assert r.tool_calls[0].arguments == {"vendor": "Northwind"}
    assert r.tool_calls[1].arguments == {"name": "Arden"}, "string arguments are parsed"
    assert r.message["tool_calls"], "the assistant turn keeps its tool calls for the next request"


def test_chat_without_tools_sends_none(captured):
    chat("x")
    assert "tools" not in captured["body"]


def test_tool_result_message():
    m = tool_result("sum_payments", {"total": "2400000.00"})
    assert m == {"role": "tool", "tool_name": "sum_payments", "content": '{"total": "2400000.00"}'}


def test_cloud_provider_refuses_tools(monkeypatch):
    monkeypatch.setitem(load_config(), "provider", "anthropic")
    with pytest.raises(SystemExit, match="Ollama or OpenRouter only"):
        chat("x", tools=[SUM_TOOL])


def test_briefing_loads():
    assert "written at 01:58:14 on" in case.read("00-briefing.md")


@pytest.mark.live
def test_live_model_calls_a_tool():
    r = chat("What is the total paid to Northwind? Use the tool.", tools=[SUM_TOOL], temperature=0)
    assert r.tool_calls and r.tool_calls[0].name == "sum_payments"
