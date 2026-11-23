"""OpenTelemetry traces for every model call and every agent step, with GenAI attributes.

Off unless `LANTERN_TRACE` names a file (`make lesson N=15 TRACE=1` writes
`.scratch/traces/15.jsonl`) or a lesson calls `enable(path)`. Each span is one JSON line, as
the OpenTelemetry SDK hands it to the exporter, so any backend that reads OTLP JSON or a
collector's file receiver can take it; nothing leaves the machine.

Attribute names follow the OpenTelemetry semantic conventions for generative AI
(`gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`,
`gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.tool.name`). What the
conventions do not name (cached tokens, cost, the latency including prompt processing) is
under `lantern.*`.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

_provider: TracerProvider | None = None


class JsonLines(SpanExporter):
    """Writes each finished span as one JSON line."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        with self.path.open("a", encoding="utf-8") as f:
            for s in spans:
                f.write(json.dumps({
                    "name": s.name, "trace_id": f"{s.context.trace_id:032x}",
                    "span_id": f"{s.context.span_id:016x}",
                    "parent_id": f"{s.parent.span_id:016x}" if s.parent else None,
                    "start_ns": s.start_time, "end_ns": s.end_time,
                    "attributes": dict(s.attributes or {}),
                    "status": s.status.status_code.name}) + "\n")
        return SpanExportResult.SUCCESS


def enable(path: Path | str) -> None:
    """Start writing spans to `path` for the rest of this process."""
    global _provider
    _provider = TracerProvider(resource=Resource.create({"service.name": "lantern"}))
    _provider.add_span_processor(SimpleSpanProcessor(JsonLines(Path(path))))


def enabled() -> bool:
    if _provider is None and os.getenv("LANTERN_TRACE"):
        enable(os.environ["LANTERN_TRACE"])
    return _provider is not None


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Any]:
    """A span when tracing is on; otherwise nothing, at no cost."""
    if not enabled():
        yield None
        return
    tracer = _provider.get_tracer("lantern")  # type: ignore[union-attr]
    with tracer.start_as_current_span(name) as s:
        for k, v in attributes.items():
            if v is not None:
                s.set_attribute(k, v)
        yield s


def record_reply(s: Any, reply: Any, provider: str) -> None:
    """Usage attributes of one model call on its span."""
    if s is None:
        return
    s.set_attribute("gen_ai.provider.name", provider)
    s.set_attribute("gen_ai.response.model", reply.model or "")
    s.set_attribute("gen_ai.usage.input_tokens", int(reply.prompt_tokens))
    s.set_attribute("gen_ai.usage.output_tokens", int(reply.output_tokens))
    s.set_attribute("lantern.cached_tokens", int(reply.cached_tokens))
    s.set_attribute("lantern.latency_s", float(reply.latency))
    s.set_attribute("lantern.prompt_seconds", float(reply.prompt_seconds))
    if reply.cost is not None:
        s.set_attribute("lantern.cost_usd", float(reply.cost))
    stop = (reply.raw or {}).get("done_reason") or (reply.raw or {}).get("stop_reason")
    if stop:
        s.set_attribute("gen_ai.response.finish_reasons", [str(stop)])


__all__ = ["enable", "enabled", "span", "record_reply", "trace"]
