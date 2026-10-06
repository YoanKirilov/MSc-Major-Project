"""Loopback-only disconnect/subprocess diagnostic; no device scans or report writes."""

import asyncio
import json
import socket
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.runtime_diagnostics import observe_asyncio_errors  # noqa: E402
from app.scanner.runner import run_process  # noqa: E402


class Echo(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self.transport.write(data)

    def eof_received(self):
        self.transport.close()


def request(port, reset):
    with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
        client.sendall(b"ping")
        reply = b""
        while len(reply) < 4:
            part = client.recv(4 - len(reply))
            assert part, "Connection closed before the echo completed"
            reply += part
        assert reply == b"ping"
        if reset:
            client.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("HH", 1, 0))
        else:
            client.shutdown(socket.SHUT_WR)
            assert client.recv(1) == b""


async def main():
    if sys.platform != "win32":
        raise SystemExit("This diagnostic targets the Windows Proactor event loop")
    loop = asyncio.get_running_loop()
    with observe_asyncio_errors(loop) as diagnostics:
        server = await loop.create_server(Echo, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        try:
            for reset in (False, True):
                for _ in range(10):
                    result, _ = await asyncio.gather(
                        run_process([sys.executable, "-c", "print('scanner-probe')"], 5),
                        asyncio.to_thread(request, port, reset),
                    )
                    assert result.returncode == 0 and b"scanner-probe" in result.stdout
                    assert not (result.timed_out or result.cancelled or result.overflow)
            await asyncio.to_thread(request, port, False)
        finally:
            server.close()
            await asyncio.wait_for(server.wait_closed(), timeout=5)
        print(
            json.dumps(
                {
                    "python": sys.version.split()[0],
                    "event_loop": type(loop).__name__,
                    "orderly_disconnects": 11,
                    "abrupt_disconnects": 10,
                    "concurrent_subprocesses_passed": 20,
                    "responsive_after_disconnects": True,
                    "diagnostics": diagnostics,
                    "limitation": (
                        "Loopback transport probe, not the full app or proof the reset is fixed"
                    ),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
