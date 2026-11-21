"""lantern.hosted: every native feature, checked offline against the documented shapes.

No call here reaches a provider. The response fixture is hand-written from Anthropic's
documented response shapes (its `_note` says so); a recorded live response replaces it once a
hosted run has been made.
"""

import json
from pathlib import Path

import pytest

from lantern import hosted

PRICES = {"input": 2.0, "output": 10.0, "cache_write_5m": 2.5, "cache_write_1h": 4.0,
          "cache_read": 0.1}
FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "hosted-response.json").read_text())
TOOL = {"type": "function", "function": {"name": "money_out", "description": "Payees.",
                                         "parameters": {"type": "object", "properties": {
                                             "file": {"type": "string"}}}}}


def conversation():
    return [{"role": "system", "content": "rules"}, {"role": "system", "content": "listing"},
            {"role": "user", "content": "trace it"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "money_out", "arguments": {"file": "a.csv"}}},
                {"function": {"name": "money_out", "arguments": '{"file": "b.csv"}'}}]},
            {"role": "tool", "tool_name": "money_out", "content": "A"},
            {"role": "tool", "tool_name": "money_out", "content": "B"}]


def test_tool_calls_get_ids_and_results_pair_with_them_in_one_user_turn():
    system, msgs = hosted.to_anthropic(conversation())
    assert [b["text"] for b in system] == ["rules", "listing"]
    uses = [b for b in msgs[1]["content"] if b["type"] == "tool_use"]
    results = msgs[2]["content"]
    assert [u["input"] for u in uses] == [{"file": "a.csv"}, {"file": "b.csv"}]
    assert [r["tool_use_id"] for r in results] == [u["id"] for u in uses]
    assert len(msgs) == 3, "two results after one assistant turn are one user turn"


def test_explicit_breakpoints_sit_on_the_stable_prefix_with_the_ttl():
    kwargs, betas, _ = hosted.build_request(conversation(), model="m", max_tokens=10,
                                            tools=[TOOL], cache="explicit", ttl="1h")
    assert kwargs["tools"][-1]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert kwargs["system"][-1]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert "cache_control" not in kwargs["system"][0], "one breakpoint, at the end of the prefix"
    assert "cache_control" not in kwargs and betas == []


def test_automatic_caching_is_the_top_level_marker():
    kwargs, _, _ = hosted.build_request(conversation(), model="m", max_tokens=10, cache="auto")
    assert kwargs["cache_control"] == {"type": "ephemeral"}
    kwargs, _, _ = hosted.build_request(conversation(), model="m", max_tokens=10, cache="none")
    assert "cache_control" not in kwargs and "cache_control" not in kwargs["system"][-1]


def test_context_editing_compaction_and_memory_are_native():
    kwargs, betas, _ = hosted.build_request(
        conversation(), model="m", max_tokens=10, tools=[TOOL], memory=True,
        clear_tool_uses={"trigger": {"type": "input_tokens", "value": 30000},
                         "keep": {"type": "tool_uses", "value": 3}},
        compact={"trigger": {"type": "input_tokens", "value": 60000}})
    edits = kwargs["context_management"]["edits"]
    assert [e["type"] for e in edits] == ["clear_tool_uses_20250919", "compact_20260112"]
    assert edits[0]["keep"] == {"type": "tool_uses", "value": 3}
    assert set(betas) == {"context-management-2025-06-27", "compact-2026-01-12"}
    assert {"type": "memory_20250818", "name": "memory"} in [
        {k: v for k, v in t.items() if k != "cache_control"} for t in kwargs["tools"]]


def test_server_compaction_below_its_minimum_trigger_is_refused_not_sent():
    with pytest.raises(ValueError, match="50,000"):
        hosted.build_request(conversation(), model="m", max_tokens=10,
                             compact={"trigger": {"type": "input_tokens", "value": 1500}})


def test_structured_output_is_native_and_strict():
    schema = {"type": "object", "properties": {"flows": {"type": "array", "items": {
        "type": "object", "properties": {"payer": {"type": "string"}}}}}}
    kwargs, _, _ = hosted.build_request(conversation(), model="m", max_tokens=10, format=schema,
                                        effort="low")
    fmt = kwargs["output_config"]["format"]
    assert fmt["type"] == "json_schema" and kwargs["output_config"]["effort"] == "low"
    item = fmt["schema"]["properties"]["flows"]["items"]
    assert item["additionalProperties"] is False and item["required"] == ["payer"]
    assert "Reply with JSON" not in json.dumps(kwargs), "no prompt imitation of the feature"


def test_settings_the_model_does_not_take_are_reported_not_dropped_in_silence():
    _, _, unsupported = hosted.build_request(
        conversation(), model="m", max_tokens=10,
        asked={"temperature": 0.2, "seed": 7, "num_ctx": 8192, "top_k": None})
    assert unsupported == ["num_ctx", "seed", "temperature"]


def test_a_response_is_read_with_cached_tokens_edits_compaction_and_cost():
    r = hosted.parse(FIXTURE, prices=PRICES, seconds=1.5)
    assert r.tool_calls[0].name == "money_out" and r.cached_tokens == 3000
    assert r.prompt_tokens == 4200
    assert r.raw["applied_edits"][0]["cleared_input_tokens"] == 9000
    assert r.raw["compactions"] and r.message["blocks"][0]["type"] == "compaction"
    # (52000 + 1200) input * 2 + (900 + 80) output * 10 + 3000 cached * 0.1, per million
    assert r.cost == pytest.approx((53200 * 2 + 980 * 10 + 3000 * 0.1) / 1e6)


def test_a_compaction_block_goes_back_whole_on_the_next_request():
    r = hosted.parse(FIXTURE, prices=PRICES)
    _, msgs = hosted.to_anthropic([{"role": "user", "content": "go"}, r.message])
    assert msgs[1]["content"][0]["type"] == "compaction"


def test_cache_writes_cost_more_on_the_long_ttl():
    usage = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 1_000_000}
    assert hosted.cost(usage, PRICES, "5m") == pytest.approx(2.5)
    assert hosted.cost(usage, PRICES, "1h") == pytest.approx(4.0)


def test_nothing_is_sent_unless_synthetic_cloud_is_allowed(monkeypatch):
    monkeypatch.setattr(hosted, "load_config", lambda: {"synthetic": {"cloud": False}})
    with pytest.raises(SystemExit, match="synthetic.cloud"):
        hosted.send([{"role": "user", "content": "x"}])


def test_config_prices_name_the_page_and_the_date():
    h = hosted.settings()
    assert h["provider"] == "anthropic" and h["prices_checked"]
    assert set(h["prices"]) == set(PRICES)


def test_lantern_chat_on_the_hosted_tier_goes_end_to_end_through_the_sdk(monkeypatch):
    """TIER=hosted: lantern.chat builds the native request, sends it through the SDK client
    and reads the reply, usage and cost back. The SDK is faked; nothing leaves the machine."""
    import sys
    import types

    from lantern import llm

    sent = {}

    class Messages:
        def create(self, **kwargs):
            sent.update(kwargs)
            return types.SimpleNamespace(to_dict=lambda: FIXTURE)

    class Client:
        def __init__(self, **kwargs):
            sent["client"] = kwargs
            self.messages = Messages()
            self.beta = types.SimpleNamespace(messages=Messages())

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=Client))
    monkeypatch.setenv("LANTERN_TIER", "hosted")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    real = hosted.load_config

    def config():
        cfg = real()
        return {**cfg, "synthetic": {"cloud": True}}

    monkeypatch.setattr(hosted, "load_config", config)
    before = llm.USAGE.calls
    r = llm.chat([{"role": "system", "content": "rules"}, {"role": "user", "content": "go"}],
                 tools=[TOOL], seed=7, temperature=0.2)
    assert r.tool_calls[0].name == "money_out" and r.cost > 0
    assert sent["model"] == "claude-sonnet-5-5" and sent["cache_control"]
    assert "temperature" not in sent and "seed" not in sent
    assert {"seed", "temperature", "num_ctx"} <= set(r.raw["unsupported"])
    assert sent["client"]["max_retries"] >= 2 and sent["client"]["timeout"]
    assert llm.USAGE.calls == before + 1
