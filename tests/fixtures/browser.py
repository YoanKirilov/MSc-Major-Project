"""Reserve loopback listeners without browser-blocked low port assignments."""

import errno
import secrets
import socket

MIN_BROWSER_PORT = 49152
MAX_BROWSER_PORT = 65535
PORT_ATTEMPTS = 64


def browser_listener():
    """Keep the socket reserved through Uvicorn startup; never probe then close.

    The default browser restricted-port lists are below this high ephemeral range.
    Custom enterprise policies are not overridden. Retry address collisions and
    OS-reserved ports only, with a bounded failure if none can be allocated.
    """
    for _ in range(PORT_ATTEMPTS):
        port = MIN_BROWSER_PORT + secrets.randbelow(MAX_BROWSER_PORT - MIN_BROWSER_PORT + 1)
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind(("127.0.0.1", port))
        except OSError as exc:
            listener.close()
            if exc.errno not in {errno.EADDRINUSE, errno.EACCES}:
                raise
        else:
            return listener
    raise RuntimeError("No browser-safe loopback test port could be reserved")
