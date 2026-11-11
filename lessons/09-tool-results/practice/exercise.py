"""Chapter 09 exercise: clear a used tool result, and say that it was cleared.

Grade it with `make exercise N=09`. The tests pass in conversations as lists of messages, so no
model is needed. When it passes, `make lesson N=09 ARGS=--mine` runs the clearing arm on yours.
"""

from __future__ import annotations

from typing import Any

Messages = list[dict[str, Any]]
CLEARED = "[Cleared to save room."
SMALL = 400  # characters; a result this short is left as it is


def stub(call: str) -> str:
    """What is left in place of a cleared result. `call` reads like statement(corvane.csv)."""
    return (f"{CLEARED} This was the result of {call}. You have already reported from it. Call "
            "it again only if you need a line of it.]")


def clear_old(messages: Messages) -> Messages:
    """Every old tool result replaced by a line saying what it was and that it was cleared.

    - The newest tool result is never cleared: the agent has not read it yet.
    - A result of SMALL characters or fewer is left alone, and so is one already cleared.
    - The stub names the call that produced the result. A tool message follows the assistant
      message whose tool_calls asked for it: [{"function": {"name": ..., "arguments": {...}}}].
      Write the call as name(value, value).
    - The list passed in is not changed, and no message is added or dropped.
    """
    # TODO 1: find the index of the newest message whose role is "tool".
    # TODO 2: walk the messages, remembering the latest call an assistant message made.
    # TODO 3: replace the content of each old, long, uncleared tool message with stub(call).
    raise NotImplementedError("write clear_old")
