"""One function, `chat`, that every lesson uses to talk to a model on LANTERN.

Carried over from Case File 02 unchanged in behaviour: pass `tools=[...]` (Ollama's function
schema) and the `Reply` carries any `tool_calls` the model asked for. In this lab every
chapter is about what goes into `messages` before the call.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import httpx

from lantern.config import load_config, model_name

Message = dict[str, Any]


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class Reply:
    text: str
    model: str
    thinking: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    prompt_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def tokens_per_second(self) -> float:
        return self.output_tokens / self.seconds if self.seconds else 0.0

    @property
    def message(self) -> Message:
        """The assistant turn to append to the conversation, tool calls included."""
        return self.raw.get("message", {"role": "assistant", "content": self.text})

    def json(self) -> Any:
        return json.loads(self.text)


def chat(
    messages: list[Message] | str,
    *,
    system: str | None = None,
    model: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    temperature: float | None = None,
    top_k: int | None = None,
    top_p: float | None = None,
    seed: int | None = None,
    num_ctx: int | None = None,
    max_tokens: int | None = None,
    think: bool | None = None,
    format: dict[str, Any] | str | None = None,
) -> Reply:
    """Send a conversation to the configured provider and return a Reply.

    `messages` may be a plain string (one user turn) or a list of message dicts.
    Any generation setting left as None falls back to config.yaml.
    """
    cfg = load_config()
    messages, settings = _prepare(
        messages,
        system,
        dict(
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            seed=seed,
            num_ctx=num_ctx,
            max_tokens=max_tokens,
            think=think,
        ),
    )
    provider = cfg["provider"]
    if provider == "ollama":
        return _ollama(messages, model_name(model), settings, tools, format)
    if provider == "openrouter":
        return _openrouter(messages, openrouter_model(model), settings, tools, format)
    if tools:
        raise SystemExit(
            "lantern.chat sends tools to Ollama or OpenRouter only. Set `provider: ollama` in "
            "config.yaml, or run with PROVIDER=openrouter."
        )
    from lantern import cloud

    return cloud.chat(provider, messages, settings, format)


def _prepare(
    messages: list[Message] | str, system: str | None, overrides: dict[str, Any]
) -> tuple[list[Message], dict[str, Any]]:
    """Turn a string into a message list, add the system message, and fill in settings."""
    gen = load_config()["generation"]
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    if system:
        messages = [{"role": "system", "content": system}, *messages]
    settings = {
        k: gen[k] if overrides.get(k) is None else overrides[k]
        for k in ("temperature", "top_k", "top_p", "seed", "num_ctx", "max_tokens", "think")
    }
    return messages, settings


def _body(
    messages: list[Message],
    model: str,
    s: dict[str, Any],
    tools: list[dict[str, Any]] | None,
    format: dict[str, Any] | str | None,
    stream: bool,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "think": s["think"],
        "options": {
            "temperature": s["temperature"],
            "top_k": s["top_k"],
            "top_p": s["top_p"],
            "num_ctx": s["num_ctx"],
            "num_predict": s["max_tokens"],
        },
    }
    if s["seed"] is not None:
        body["options"]["seed"] = s["seed"]
    if tools:
        body["tools"] = tools
    if format is not None:
        body["format"] = format
    return body


@dataclass
class Chunk:
    """One piece of a streamed reply. The last one has done=True and the token counts."""

    text: str = ""
    thinking: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    done: bool = False
    prompt_tokens: int = 0
    output_tokens: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


def stream(
    messages: list[Message] | str,
    *,
    system: str | None = None,
    model: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    **overrides: Any,
) -> Iterator[Chunk]:
    """Like `chat`, but yield the reply piece by piece as Ollama sends it.

    Stop iterating and the HTTP connection is closed. Ollama only, like tool calling.
    """
    messages, s = _prepare(messages, system, overrides)
    cfg = load_config()
    if cfg["provider"] != "ollama":
        raise SystemExit(
            "lantern.stream reads Ollama's stream only. Run it without "
            "LANTERN_PROVIDER, or with LANTERN_PROVIDER=ollama."
        )
    body = _body(messages, model_name(model), s, tools, None, stream=True)
    url = f"{cfg['ollama']['host']}/api/chat"
    with httpx.stream("POST", url, json=body, timeout=cfg["limits"]["request_timeout_s"]) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            msg = data.get("message", {})
            yield Chunk(
                text=msg.get("content") or "",
                thinking=msg.get("thinking") or "",
                tool_calls=[
                    ToolCall(c["function"]["name"], _args(c["function"].get("arguments")))
                    for c in msg.get("tool_calls") or []
                ],
                done=bool(data.get("done")),
                prompt_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
                raw=data,
            )


def _ollama(
    messages: list[Message],
    model: str,
    s: dict[str, Any],
    tools: list[dict[str, Any]] | None,
    format: dict[str, Any] | str | None,
) -> Reply:
    body = _body(messages, model, s, tools, format, stream=False)
    host = load_config()["ollama"]["host"]
    try:
        r = httpx.post(
            f"{host}/api/chat", json=body, timeout=load_config()["limits"]["request_timeout_s"]
        )
    except httpx.ConnectError as e:
        raise SystemExit(
            f"Cannot reach Ollama at {host}. Start it with `make up` (Docker) or `ollama serve`."
        ) from e
    except httpx.TimeoutException as e:
        raise SystemExit(
            f"Ollama did not answer within limits.request_timeout_s; the request was cancelled. "
            f"On CPU, try LANTERN_MODEL={load_config()['models']['small']}."
        ) from e
    if r.status_code == 404:
        raise SystemExit(f"Model {model!r} is not pulled. Run `make models`.")
    r.raise_for_status()
    data = r.json()
    msg = data["message"]
    calls = [
        ToolCall(c["function"]["name"], _args(c["function"].get("arguments")))
        for c in msg.get("tool_calls") or []
    ]
    return Reply(
        text=(msg.get("content") or "").strip(),
        thinking=msg.get("thinking", "") or "",
        tool_calls=calls,
        model=model,
        prompt_tokens=data.get("prompt_eval_count", 0),
        output_tokens=data.get("eval_count", 0),
        seconds=data.get("eval_duration", 0) / 1e9,
        raw=data,
    )


def _args(value: Any) -> dict[str, Any]:
    """Ollama returns arguments as an object; some models emit a JSON string instead."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {"_unparsed": value}
    return dict(value or {})


def openrouter_model(alias_or_name: str | None) -> str:
    """The OpenRouter model for an alias or a local name; OpenRouter ids (with a /) pass through.

    `default` and the configured local default map to `openrouter.model`; `small` and the local
    small model to `openrouter.small_model`. Any other name is sent as it is.
    """
    cfg = load_config()
    local, remote = cfg["models"], cfg["openrouter"]
    if alias_or_name in (None, "default", local["default"]):
        return remote["model"]
    if alias_or_name in ("small", local.get("small")):
        return remote.get("small_model", remote["model"])
    return alias_or_name


def to_openai(messages: list[Message]) -> list[dict[str, Any]]:
    """Ollama-style messages as OpenAI chat messages.

    OpenAI's format pairs every tool result with the id of the call it answers. Lantern's
    messages carry no ids, so each call gets one (or keeps the one OpenRouter gave it) and each
    tool message takes the next unanswered id. A tool result with no call before it (which
    compaction should never leave) becomes a user message rather than a request the API refuses.
    """
    out: list[dict[str, Any]] = []
    pending: list[str] = []
    n = 0
    for m in messages:
        role = m.get("role")
        if role == "assistant":
            calls = []
            for c in m.get("tool_calls") or []:
                n += 1
                f = c.get("function", {})
                args = f.get("arguments")
                cid = c.get("id") or f"call_{n}"
                calls.append({
                    "id": cid,
                    "type": "function",
                    "function": {
                        "name": f.get("name", ""),
                        "arguments": args if isinstance(args, str) else json.dumps(args or {}),
                    },
                })
                pending.append(cid)
            msg: dict[str, Any] = {"role": "assistant", "content": m.get("content") or ""}
            if calls:
                msg["tool_calls"] = calls
            out.append(msg)
        elif role == "tool":
            content = m.get("content") or ""
            if pending:
                out.append({"role": "tool", "tool_call_id": pending.pop(0), "content": content})
            else:
                out.append({"role": "user", "content": f"Tool result: {content}"})
        else:
            out.append({"role": role, "content": m.get("content") or ""})
    return out


def _openrouter(
    messages: list[Message],
    model: str,
    s: dict[str, Any],
    tools: list[dict[str, Any]] | None,
    format: dict[str, Any] | str | None,
) -> Reply:
    import os
    import time

    cfg = load_config()
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        raise SystemExit("LANTERN_PROVIDER=openrouter needs OPENROUTER_API_KEY in .env.")
    body: dict[str, Any] = {
        "model": model,
        "messages": to_openai(messages),
        "temperature": s["temperature"],
        "top_p": s["top_p"],
        "top_k": s["top_k"],
        "max_tokens": s["max_tokens"],
        "usage": {"include": True},  # OpenRouter adds the cost of the call to `usage`
    }
    if s["seed"] is not None:
        body["seed"] = s["seed"]
    if tools:
        body["tools"] = tools
    if s["think"]:
        body["reasoning"] = {"enabled": True}
    if isinstance(format, dict):
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "reply", "schema": format, "strict": True},
        }
    elif format == "json":
        body["response_format"] = {"type": "json_object"}
    start = time.perf_counter()
    try:
        r = httpx.post(
            f"{cfg['openrouter']['base_url']}/chat/completions",
            json=body,
            headers={"Authorization": f"Bearer {key}", "X-Title": "context-lab"},
            timeout=cfg["limits"]["request_timeout_s"],
        )
    except httpx.TimeoutException as e:
        raise SystemExit("OpenRouter did not answer within limits.request_timeout_s.") from e
    if r.status_code in (401, 402, 403):
        raise SystemExit(f"OpenRouter refused the request ({r.status_code}): {r.text[:200]}")
    if r.status_code in (400, 404) and "model" in r.text.lower():
        raise SystemExit(f"OpenRouter has no model {model!r}: {r.text[:200]}")
    r.raise_for_status()
    data = r.json()
    if "error" in data and not data.get("choices"):
        raise SystemExit(f"OpenRouter error: {json.dumps(data['error'])[:300]}")
    out = data["choices"][0]["message"]
    calls = [
        ToolCall(c["function"]["name"], _args(c["function"].get("arguments")))
        for c in out.get("tool_calls") or []
    ]
    # Kept in lantern's own (Ollama) shape, ids included, so the next call can pair results.
    msg: Message = {"role": "assistant", "content": out.get("content") or ""}
    if calls:
        msg["tool_calls"] = [
            {"id": c.get("id"), "function": {"name": t.name, "arguments": t.arguments}}
            for c, t in zip(out["tool_calls"], calls, strict=True)
        ]
    usage = data.get("usage") or {}
    return Reply(
        text=(out.get("content") or "").strip(),
        thinking=out.get("reasoning") or "",
        tool_calls=calls,
        model=data.get("model", model),
        prompt_tokens=usage.get("prompt_tokens", 0),
        output_tokens=usage.get("completion_tokens", 0),
        seconds=time.perf_counter() - start,
        raw={"message": msg, "usage": usage, "provider": "openrouter"},
    )


def tool_result(name: str, content: Any) -> Message:
    """The message that carries a tool's result back to the model."""
    text = content if isinstance(content, str) else json.dumps(content)
    return {"role": "tool", "tool_name": name, "content": text}
