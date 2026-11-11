"""LANTERN: the Economic Offences Wing's offline analysis workstation, Case File 06.

A thin, readable client over a local Ollama server, with tool calling, used by every
lesson in this lab. The context builder and the memory store of this case file are built on
it, chapter by chapter.
"""

from lantern.config import load_config
from lantern.llm import Chunk, Reply, ToolCall, chat, stream, tool_result

__all__ = ["Chunk", "Reply", "ToolCall", "chat", "load_config", "stream", "tool_result"]
