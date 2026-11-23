"""lantern.network: every lookup and connection counted, and the ones off the machine refused."""

import socket
import threading

import pytest

from lantern import network


def test_names_and_addresses_on_this_machine_are_local():
    for host in ("localhost", "127.0.0.1", "::1", "[::1]", "ollama.localhost", b"127.0.0.2"):
        assert network.is_local(host), host
    for host in ("us.i.posthog.com", "203.0.113.7", "2001:db8::1", "api.anthropic.com"):
        assert not network.is_local(host), host


def test_an_outside_name_is_refused_before_any_lookup():
    with network.watch() as net, pytest.raises(socket.gaierror):
        socket.getaddrinfo("us.i.posthog.com", 443)
    assert net.outside == ["us.i.posthog.com"] and net.refused == ["us.i.posthog.com"]


def test_an_outside_address_is_refused_before_any_packet():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with network.watch() as net, pytest.raises(ConnectionRefusedError):
            s.connect(("203.0.113.7", 80))  # TEST-NET-3: never routed
    finally:
        s.close()
    assert net.connections == [("203.0.113.7", 80)] and net.summary()["outside_attempts"] == 1


def test_a_local_connection_is_counted_and_let_through():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    try:
        with network.watch() as net:
            c = socket.create_connection(("127.0.0.1", port), timeout=2)
            c.close()
    finally:
        server.close()
    assert net.local == [("127.0.0.1", port)] and not net.outside


def test_other_threads_are_watched_too():
    errors = []

    def call():
        try:
            socket.getaddrinfo("raw.githubusercontent.com", 443)
        except socket.gaierror as e:
            errors.append(e)

    with network.watch() as net:
        t = threading.Thread(target=call)
        t.start()
        t.join()
    assert errors and net.outside == ["raw.githubusercontent.com"]


def test_the_patch_is_taken_down_afterwards():
    real = socket.getaddrinfo
    with network.watch():
        assert socket.getaddrinfo is not real
    assert socket.getaddrinfo is real and "connect" not in vars(socket.socket)
