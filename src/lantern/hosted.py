"""The hosted tier: the same chapters on a current hosted model, using its native features.

`make lesson N=NN TIER=hosted` sets LANTERN_TIER=hosted, and `lantern.chat` sends every call
here. The provider is Anthropic (config.yaml `hosted:`). Nothing here imitates a feature in the
prompt: structured outputs go in `output_config.format`, tools are native tools, caching is
`cache_control`, clearing old tool results is context editing, compaction is the server's.

The request is built and the response is read by plain functions over dicts, so every native
feature is tested offline against the documented shapes (tests/test_hosted.py). Only `send`
needs a key and the `anthropic` SDK (`uv sync --extra cloud`); the SDK retries 408, 409, 429
and 5xx with exponential backoff and jitter, and the client sets the timeout from config.yaml.

What a provider does not support is reported, never dropped in silence: `Reply.raw
["unsupported"]` lists every setting that was asked for and not sent (on current Claude
models: temperature, top_k, top_p, seed and num_ctx), and `lantern.chat` prints it once.

Evidence never leaves LANTERN. `send` refuses to run unless `synthetic.cloud` is true in
config.yaml, which the learner sets for the synthetic case material of this lab.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from lantern.config import load_config

Message = dict[str, Any]
BETA_CONTEXT = "context-management-2025-06-27"
BETA_COMPACT = "compact-2026-01-12"
CLEAR_TOOL_USES = "clear_tool_uses_20250919"
COMPACT = "compact_20260112"
MEMORY_TOOL = {"type": "memory_20250818", "name": "memory"}
NOT_SENT = ("temperature", "top_k", "top_p", "seed", "num_ctx")
_warned: set[str] = set()


def settings() -> dict[str, Any]:
    """config.yaml `hosted:`: provider, model, prices and the native features to use."""
    return load_config()["hosted"]


# ---- the request ------------------------------------------------------------------------------


def tool_def(schema: dict[str, Any]) -> dict[str, Any]:
    """An Ollama-shaped function schema as an Anthropic tool. Already-native tools (a `type`
    such as memory_20250818) pass through."""
    if "type" in schema and schema["type"] != "function":
        return schema
    f = schema.get("function", schema)
    return {"name": f["name"], "description": f.get("description", ""),
            "input_schema": f.get("parameters") or {"type": "object", "properties": {}}}


def to_anthropic(messages: list[Message]) -> tuple[list[dict[str, Any]], list[Message]]:
    """lantern's messages (Ollama's shape) as Anthropic system blocks and messages.

    Tool calls get ids (`toolu_<n>`) in order, and each tool result is paired with the oldest
    call that has no result yet, as Ollama pairs them. Consecutive tool results go in one user
    turn, which is what the API requires after a turn with several calls.
    """
    system: list[dict[str, Any]] = []
    out: list[Message] = []
    pending: list[str] = []
    n = 0
    for m in messages:
        role = m["role"]
        if role == "system":
            system.append({"type": "text", "text": m["content"]})
        elif role == "assistant":
            blocks: list[dict[str, Any]] = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for c in m.get("tool_calls") or []:
                n += 1
                cid = c.get("id") or f"toolu_{n:04d}"
                pending.append(cid)
                args = c["function"].get("arguments") or {}
                blocks.append({"type": "tool_use", "id": cid, "name": c["function"]["name"],
                               "input": json.loads(args) if isinstance(args, str) else args})
            if m.get("blocks"):  # a hosted reply kept whole (compaction blocks must go back)
                blocks = m["blocks"]
            out.append({"role": "assistant", "content": blocks or [{"type": "text",
                                                                    "text": ""}]})
        elif role == "tool":
            cid = pending.pop(0) if pending else f"toolu_orphan_{len(out)}"
            block = {"type": "tool_result", "tool_use_id": cid, "content": m["content"]}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list) \
                    and out[-1]["content"] and out[-1]["content"][0].get("type") == "tool_result":
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        else:
            out.append({"role": "user", "content": m["content"]})
    return system, out


def build_request(messages: list[Message], *, model: str, max_tokens: int,
                  tools: list[dict[str, Any]] | None = None,
                  format: dict[str, Any] | str | None = None,
                  cache: str = "auto", ttl: str = "5m",
                  clear_tool_uses: dict[str, Any] | None = None,
                  compact: dict[str, Any] | None = None,
                  memory: bool = False, effort: str | None = None,
                  asked: dict[str, Any] | None = None
                  ) -> tuple[dict[str, Any], list[str], list[str]]:
    """The keyword arguments for `client.beta.messages.create`, the betas, and the settings
    asked for that this provider does not take.

    - `cache`: "explicit" puts a breakpoint on the last tool and the last system block (the
      stable prefix), "auto" also sets top-level automatic caching for the growing
      conversation, "none" caches nothing. `ttl` is "5m" or "1h" on every breakpoint.
    - `clear_tool_uses`: context editing; {} for the defaults, or trigger/keep/clear_at_least.
    - `compact`: server-side compaction; {} for the defaults, or trigger/instructions.
    - `memory`: adds the client-side memory tool (memory_20250818).
    - `format`: a JSON schema as native structured output (`output_config.format`).
    """
    system, msgs = to_anthropic(messages)
    kwargs: dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": msgs}
    betas: list[str] = []
    marker: dict[str, Any] = {"type": "ephemeral"} if ttl == "5m" else {"type": "ephemeral",
                                                                         "ttl": ttl}
    defs = [tool_def(t) for t in tools or []]
    if memory:
        defs.append(dict(MEMORY_TOOL))
    if cache in ("explicit", "auto"):
        if defs:
            defs[-1] = {**defs[-1], "cache_control": marker}
        if system:
            system[-1] = {**system[-1], "cache_control": marker}
    if cache == "auto":
        kwargs["cache_control"] = marker
    if system:
        kwargs["system"] = system
    if defs:
        kwargs["tools"] = defs
    output_config: dict[str, Any] = {}
    if isinstance(format, dict):
        output_config["format"] = {"type": "json_schema", "schema": strict(format)}
    elif format == "json":
        output_config["format"] = {"type": "json_schema", "schema": {"type": "object"}}
    if effort:
        output_config["effort"] = effort
    if output_config:
        kwargs["output_config"] = output_config
    edits = []
    if clear_tool_uses is not None:
        edits.append({"type": CLEAR_TOOL_USES, **clear_tool_uses})
        betas.append(BETA_CONTEXT)
    if compact is not None:
        trigger = (compact.get("trigger") or {}).get("value", 150000)
        if trigger < 50000:
            raise ValueError(f"server compaction triggers at 50,000 tokens or more, not {trigger}")
        edits.append({"type": COMPACT, **compact})
        betas.append(BETA_COMPACT)
    if edits:
        kwargs["context_management"] = {"edits": edits}
    unsupported = sorted(k for k, v in (asked or {}).items() if k in NOT_SENT and v is not None)
    return kwargs, betas, unsupported


def strict(schema: dict[str, Any]) -> dict[str, Any]:
    """A JSON schema as structured outputs needs it: every object closed
    (`additionalProperties: false`) and every property required."""
    if not isinstance(schema, dict):
        return schema
    out = {k: strict(v) if isinstance(v, dict) else v for k, v in schema.items()}
    if out.get("type") == "object":
        props = out.get("properties", {})
        out["properties"] = {k: strict(v) for k, v in props.items()}
        out["additionalProperties"] = False
        out["required"] = list(props)
    if out.get("type") == "array" and isinstance(out.get("items"), dict):
        out["items"] = strict(out["items"])
    return out


# ---- the response -----------------------------------------------------------------------------


def cost(usage: dict[str, Any], prices: dict[str, float], ttl: str = "5m") -> float:
    """US dollars for one response's usage. Every entry in `usage.iterations` is billed (a
    server compaction is a call of its own); cache writes at the TTL's price, cache reads at
    the read price. `prices` are dollars per million tokens, from config.yaml."""
    write = prices["cache_write_1h"] if ttl == "1h" else prices["cache_write_5m"]
    parts = usage.get("iterations") or [usage]
    total = 0.0
    for u in parts:
        total += (u.get("input_tokens", 0) * prices["input"]
                  + u.get("cache_creation_input_tokens", 0) * write
                  + u.get("cache_read_input_tokens", 0) * prices["cache_read"]
                  + u.get("output_tokens", 0) * prices["output"])
    if usage.get("iterations"):  # cache figures are reported once, on the top level
        total += (usage.get("cache_creation_input_tokens", 0) * write
                  + usage.get("cache_read_input_tokens", 0) * prices["cache_read"])
    return total / 1e6


def parse(data: dict[str, Any], *, prices: dict[str, float], ttl: str = "5m",
          seconds: float = 0.0, unsupported: list[str] | None = None) -> Any:
    """A response (as a dict) as a lantern Reply: text, tool calls in lantern's shape, input,
    cached and output tokens, cost, the edits the server applied, and any compaction block."""
    from lantern.llm import Reply, ToolCall

    blocks = data.get("content") or []
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    calls, tool_calls = [], []
    for b in blocks:
        if b.get("type") == "tool_use":
            calls.append(ToolCall(b["name"], b.get("input") or {}))
            tool_calls.append({"id": b["id"], "function": {"name": b["name"],
                                                           "arguments": b.get("input") or {}}})
    usage = data.get("usage") or {}
    compactions = [b.get("content") for b in blocks if b.get("type") == "compaction"]
    msg: Message = {"role": "assistant", "content": text}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    if compactions:
        msg["blocks"] = blocks  # sent back whole: the server drops what the block replaced
    prompt = (usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
              + usage.get("cache_creation_input_tokens", 0))
    return Reply(
        text=text.strip(), model=data.get("model", ""), tool_calls=calls,
        prompt_tokens=prompt, output_tokens=usage.get("output_tokens", 0),
        seconds=seconds, latency=seconds,
        cached_tokens=usage.get("cache_read_input_tokens", 0),
        cache_write_tokens=usage.get("cache_creation_input_tokens", 0),
        cost=cost(usage, prices, ttl),
        raw={"message": msg, "usage": usage, "provider": "anthropic",
             "stop_reason": data.get("stop_reason"),
             "applied_edits": (data.get("context_management") or {}).get("applied_edits", []),
             "compactions": compactions, "unsupported": unsupported or []},
    )


# ---- sending ----------------------------------------------------------------------------------


def send(messages: list[Message], *, tools: list[dict[str, Any]] | None = None,
         format: dict[str, Any] | str | None = None, max_tokens: int = 1200,
         asked: dict[str, Any] | None = None, **features: Any) -> Any:
    """One call on the hosted model. `features` override config.yaml `hosted.features`."""
    cfg = load_config()
    if not cfg.get("synthetic", {}).get("cloud"):
        raise SystemExit("TIER=hosted sends this chapter's material to Anthropic. Set "
                         "`synthetic.cloud: true` in config.yaml to allow it (the lab's case is "
                         "synthetic; in the story, evidence never leaves LANTERN).")
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("TIER=hosted needs ANTHROPIC_API_KEY in .env (see .env.example).")
    try:
        import anthropic
    except ImportError as e:
        raise SystemExit("TIER=hosted needs the SDK: uv sync --extra cloud") from e
    h = settings()
    opts = {**h.get("features", {}), **features}
    kwargs, betas, unsupported = build_request(
        messages, model=h["model"], max_tokens=max_tokens, tools=tools, format=format,
        cache=opts.get("cache", "auto"), ttl=opts.get("ttl", "5m"),
        clear_tool_uses=opts.get("clear_tool_uses"), compact=opts.get("compact"),
        memory=opts.get("memory", False), effort=opts.get("effort"), asked=asked)
    for k in unsupported:
        if k not in _warned:
            _warned.add(k)
            print(f"[hosted] {h['model']} does not take {k}; it was not sent.")
    client = anthropic.Anthropic(timeout=cfg["limits"]["request_timeout_s"], max_retries=4)
    start = time.perf_counter()
    r = client.beta.messages.create(**kwargs, betas=betas) if betas else \
        client.messages.create(**kwargs)
    return parse(r.to_dict(), prices=h["prices"], ttl=opts.get("ttl", "5m"),
                 seconds=time.perf_counter() - start, unsupported=unsupported)
