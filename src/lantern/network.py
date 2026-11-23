"""Every network connection a block of code tries to open, counted, and those leaving the machine
refused.

Chapter 21 runs memory libraries on the case. Memory is evidence, so a library is run only if
nothing it does leaves the machine. `watch()` patches the two calls every Python network client
ends in (`socket.getaddrinfo` for a name, `socket.socket.connect` for an address), for every
thread, while the block runs:

    with network.watch() as net:
        memory.add(...)
    net.outside       # names and addresses off this machine that were asked for (and refused)
    net.local         # connections to this machine (Ollama on localhost)

It does what decision 0003's refusing proxy did, inside the process: a library that tries to
send telemetry is counted and stopped, not trusted to have been switched off. It sees only
Python's socket module; a library that opened sockets from C code of its own would not be seen.
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

LOCAL_NAMES = {"localhost", "localhost.localdomain", "ip6-localhost", ""}


def is_local(host: Any) -> bool:
    """A name or an address on this machine: localhost, a loopback address, a .localhost name."""
    name = host.decode() if isinstance(host, bytes) else str(host)
    name = name.strip("[]").lower()
    if name in LOCAL_NAMES or name.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(name.split("%")[0]).is_loopback
    except ValueError:
        return False


@dataclass
class Net:
    """What a watched block asked for: name lookups, connections, and what was refused."""

    lookups: list[str] = field(default_factory=list)
    connections: list[tuple[str, int | None]] = field(default_factory=list)
    refused: list[str] = field(default_factory=list)

    @property
    def outside(self) -> list[str]:
        """Every name or address off this machine that was asked for, in order."""
        names = [n for n in self.lookups if not is_local(n)]
        names += [h for h, _ in self.connections if not is_local(h)]
        return names

    @property
    def local(self) -> list[tuple[str, int | None]]:
        return [(h, p) for h, p in self.connections if is_local(h)]

    def summary(self) -> dict[str, Any]:
        return {"lookups": len(self.lookups), "connections": len(self.connections),
                "local_connections": len(self.local), "outside_attempts": len(self.outside),
                "outside_hosts": sorted(set(self.outside)), "refused": len(self.refused)}


@contextmanager
def watch(refuse_outside: bool = True) -> Iterator[Net]:
    """Count every lookup and connection made while the block runs, in every thread. With
    `refuse_outside`, a lookup of a name off this machine fails as an unknown name, and a
    connection to an address off it is refused, before anything is sent."""
    net = Net()
    real_lookup = socket.getaddrinfo
    had_connect = "connect" in vars(socket.socket)
    real_connect = socket.socket.connect

    def lookup(host: Any, port: Any, *args: Any, **kwargs: Any) -> Any:
        name = host.decode() if isinstance(host, bytes) else str(host or "")
        net.lookups.append(name)
        if refuse_outside and not is_local(name):
            net.refused.append(name)
            raise socket.gaierror(socket.EAI_NONAME, f"refused by lantern.network: {name}")
        return real_lookup(host, port, *args, **kwargs)

    def connect(self: socket.socket, address: Any) -> Any:
        if self.family not in (socket.AF_INET, socket.AF_INET6):
            return real_connect(self, address)
        host, port = str(address[0]), int(address[1])
        net.connections.append((host, port))
        if refuse_outside and not is_local(host):
            net.refused.append(host)
            raise ConnectionRefusedError(f"refused by lantern.network: {host}:{port}")
        return real_connect(self, address)

    socket.getaddrinfo = lookup  # type: ignore[assignment]
    socket.socket.connect = connect  # type: ignore[method-assign]
    try:
        yield net
    finally:
        socket.getaddrinfo = real_lookup  # type: ignore[assignment]
        if had_connect:
            socket.socket.connect = real_connect  # type: ignore[method-assign]
        else:
            del socket.socket.connect


__all__ = ["Net", "is_local", "watch"]
