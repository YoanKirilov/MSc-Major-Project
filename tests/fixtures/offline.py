"""Fail closed if a synthetic test accidentally attempts real discovery or traffic."""

import asyncio
import ipaddress
import os
import socket
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path


class OfflineAccessError(AssertionError):
    pass


def require_loopback(host):
    # Resolve no external name, including a hostname that might resolve locally.
    if isinstance(host, bytes):
        host = host.decode("ascii", errors="replace")
    if host == "localhost":
        return
    try:
        address = ipaddress.ip_address(host)
    except (ValueError, TypeError):
        raise OfflineAccessError("Offline tests may not resolve external hostnames") from None
    if not address.is_loopback:
        raise OfflineAccessError("Offline tests may not contact non-loopback addresses")


def browser_driver_executable():
    """Permit only Playwright's packaged driver when browser tests explicitly opt in."""
    spec = find_spec("playwright")
    if spec is None or spec.origin is None:
        return None
    return Path(spec.origin).parent / "driver" / ("node.exe" if os.name == "nt" else "node")


def install_offline_guard(monkeypatch, *, allow_browser=False):
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex
    sendto = socket.socket.sendto
    getaddrinfo = socket.getaddrinfo
    resolvers = {
        name: getattr(socket, name)
        for name in ("gethostbyname", "gethostbyname_ex", "gethostbyaddr")
    }
    popen_init = subprocess.Popen.__init__
    create_connection = asyncio.BaseEventLoop.create_connection
    create_datagram = asyncio.BaseEventLoop.create_datagram_endpoint
    allowed_executables = {os.path.normcase(os.path.abspath(sys.executable))}
    if allow_browser and (driver := browser_driver_executable()) is not None:
        allowed_executables.add(os.path.normcase(os.path.abspath(driver)))

    def check_address(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            require_loopback(address[0])

    def guarded_connect(sock, address):
        check_address(sock, address)
        return connect(sock, address)

    def guarded_connect_ex(sock, address):
        check_address(sock, address)
        return connect_ex(sock, address)

    def guarded_sendto(sock, data, *args):
        check_address(sock, args[-1])
        return sendto(sock, data, *args)

    def guarded_getaddrinfo(host, *args, **kwargs):
        if host is not None:  # None can be a passive local listener, not a probe.
            require_loopback(host)
        return getaddrinfo(host, *args, **kwargs)

    def guarded_popen(process, args, *extra, **kwargs):
        # Runner tests use only this interpreter with synthetic code. Explicit
        # browser tests additionally use their packaged driver, never a scanner/shell.
        executable = kwargs.get("executable") or (
            args[0] if isinstance(args, (list, tuple)) and args else None
        )
        if (
            kwargs.get("shell")
            or executable is None
            or os.path.normcase(os.path.abspath(executable)) not in allowed_executables
        ):
            raise OfflineAccessError("Offline tests may launch only approved test processes")
        return popen_init(process, args, *extra, **kwargs)

    async def guarded_connection(loop, protocol_factory, host=None, port=None, **kwargs):
        if host is not None:
            require_loopback(host)
        return await create_connection(loop, protocol_factory, host, port, **kwargs)

    async def guarded_datagram(loop, protocol_factory, local_addr=None, remote_addr=None, **kwargs):
        if remote_addr is not None:
            require_loopback(remote_addr[0])
        return await create_datagram(
            loop, protocol_factory, local_addr=local_addr, remote_addr=remote_addr, **kwargs
        )

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    monkeypatch.setattr(socket.socket, "sendto", guarded_sendto)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    for name, resolver in resolvers.items():

        def guarded_resolver(host, resolver=resolver):
            require_loopback(host)
            return resolver(host)

        monkeypatch.setattr(socket, name, guarded_resolver)
    monkeypatch.setattr(subprocess.Popen, "__init__", guarded_popen)
    monkeypatch.setattr(asyncio.BaseEventLoop, "create_connection", guarded_connection)
    monkeypatch.setattr(asyncio.BaseEventLoop, "create_datagram_endpoint", guarded_datagram)
