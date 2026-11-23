"""Retries for every model call: a timeout, backoff with full jitter, and Retry-After honoured.

A rate limit (429) or a server error (500, 502, 503, 504, 529) or a dropped connection is retried
up to `attempts` times. The wait before attempt n is a random time between 0 and
`base * 2 ** n` seconds, capped at `cap` (full jitter: many clients that failed together do not
retry together). A `Retry-After` header, when the server sends one, is the least it waits.
Anything else (400, 401, 404) is not retried: the same request would fail the same way.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import httpx

RETRY_STATUS = frozenset({408, 409, 429, 500, 502, 503, 504, 529})


def wait_for(attempt: int, *, base: float = 1.0, cap: float = 30.0,
             retry_after: str | None = None, rand: Callable[[], float] = random.random) -> float:
    """Seconds to wait before retry `attempt` (0 for the first retry)."""
    wait = rand() * min(cap, base * 2 ** attempt)
    if retry_after:
        try:
            wait = max(wait, float(retry_after))
        except ValueError:
            pass
    return wait


def post(url: str, *, attempts: int = 4, base: float = 1.0, cap: float = 30.0,
         sleep: Callable[[float], None] | None = None,
         send: Callable[..., httpx.Response] | None = None, **kwargs: Any) -> httpx.Response:
    """`httpx.post(url, **kwargs)` with retries. The last error or response is returned or
    raised as it came, so callers keep their own messages for timeouts and refusals."""
    send = send or httpx.post
    sleep = sleep or time.sleep
    for attempt in range(attempts):
        last = attempt == attempts - 1
        try:
            r = send(url, **kwargs)
        except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError,
                httpx.TimeoutException):
            if last:
                raise
            sleep(wait_for(attempt, base=base, cap=cap))
            continue
        if r.status_code not in RETRY_STATUS or last:
            return r
        sleep(wait_for(attempt, base=base, cap=cap, retry_after=r.headers.get("retry-after")))
    raise AssertionError("unreachable")


@contextmanager
def stream(method: str, url: str, *, attempts: int = 4, base: float = 1.0, cap: float = 30.0,
           sleep: Callable[[float], None] | None = None,
           opener: Callable[..., Any] | None = None, **kwargs: Any) -> Iterator[httpx.Response]:
    """`httpx.stream(method, url, **kwargs)` with the same retries, before the first byte only.

    A refused or failed connection, or a retryable status, is retried as `post` does. Once a
    response with any other status is open, it is handed over as it is: a stream that breaks
    after some of the reply was read is not sent again, since the caller has used that part.
    """
    opener = opener or httpx.stream
    sleep = sleep or time.sleep
    for attempt in range(attempts):
        last = attempt == attempts - 1
        try:
            cm = opener(method, url, **kwargs)
            r = cm.__enter__()
        except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError,
                httpx.TimeoutException):
            if last:
                raise
            sleep(wait_for(attempt, base=base, cap=cap))
            continue
        if r.status_code in RETRY_STATUS and not last:
            cm.__exit__(None, None, None)
            sleep(wait_for(attempt, base=base, cap=cap, retry_after=r.headers.get("retry-after")))
            continue
        try:
            yield r
        finally:
            cm.__exit__(None, None, None)
        return
