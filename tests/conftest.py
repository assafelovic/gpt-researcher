"""Shared pytest configuration.

Opt-in network kill-switch: set GPTR_BLOCK_NETWORK=1 to make any outbound
socket connection raise. CI turns this on so the "offline" suite is proven
offline rather than assumed -- a test that quietly reaches a real search or
LLM endpoint is both flaky and billable, and we would rather it fail loudly
on the pull request than pass slowly and charge someone.

Loopback is left open so a test may still spin up a local server.
"""
import os
import socket

_ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost", ""}


class NetworkBlocked(RuntimeError):
    """Raised when a test attempts a non-loopback connection."""


def pytest_configure(config):
    if os.environ.get("GPTR_BLOCK_NETWORK") != "1":
        return

    real_connect = socket.socket.connect

    def guarded_connect(self, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if host in _ALLOWED_HOSTS:
            return real_connect(self, address, *args, **kwargs)
        raise NetworkBlocked(
            f"outbound connection to {address!r} blocked by GPTR_BLOCK_NETWORK. "
            "Mock the client, or move this test to the live suite."
        )

    socket.socket.connect = guarded_connect
