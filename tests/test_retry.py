"""lantern.retry: what is retried, how long it waits, and what is not retried."""

import httpx
import pytest

from lantern import retry


def response(status, headers=None):
    return httpx.Response(status, headers=headers or {}, request=httpx.Request("POST", "http://x"))


def sender(*outcomes):
    calls = []

    def send(url, **kwargs):
        calls.append(url)
        out = outcomes[len(calls) - 1]
        if isinstance(out, Exception):
            raise out
        return out
    return send, calls


def test_a_rate_limit_is_retried_and_retry_after_is_the_least_it_waits():
    waits = []
    send, calls = sender(response(429, {"retry-after": "7"}), response(200))
    r = retry.post("http://x", send=send, sleep=waits.append)
    assert r.status_code == 200 and len(calls) == 2
    assert waits[0] >= 7, "Retry-After is a floor on the wait"


def test_server_errors_and_dropped_connections_are_retried_up_to_the_limit():
    waits = []
    send, calls = sender(httpx.ConnectError("down"), response(503), response(500), response(502))
    r = retry.post("http://x", send=send, sleep=waits.append, attempts=4)
    assert r.status_code == 502 and len(calls) == 4 and len(waits) == 3


def test_a_client_error_is_not_retried():
    send, calls = sender(response(400), response(200))
    assert retry.post("http://x", send=send, sleep=lambda s: None).status_code == 400
    assert len(calls) == 1


def test_the_last_timeout_is_raised_as_it_came():
    send, _ = sender(httpx.ReadTimeout("slow"), httpx.ReadTimeout("slow"))
    with pytest.raises(httpx.TimeoutException):
        retry.post("http://x", send=send, sleep=lambda s: None, attempts=2)


def test_backoff_has_full_jitter_and_a_cap():
    assert retry.wait_for(0, base=1, rand=lambda: 1.0) == 1
    assert retry.wait_for(3, base=1, rand=lambda: 1.0) == 8
    assert retry.wait_for(10, base=1, cap=30, rand=lambda: 1.0) == 30
    assert retry.wait_for(3, base=1, rand=lambda: 0.0) == 0
