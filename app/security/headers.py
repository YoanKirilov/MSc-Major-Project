"""HTTP response defences shared by normal responses and unexpected errors."""

from app.build_info import API_CONTRACT_VERSION
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

LOCAL_RESPONSE_HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
        "img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; "
        "base-uri 'none'; form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "X-NetGuard-Contract": str(API_CONTRACT_VERSION),
}


class LocalResponseHeaders:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        async def protected_send(message: Message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in LOCAL_RESPONSE_HEADERS.items():
                    headers[name] = value
                build = getattr(getattr(scope.get("app"), "state", None), "running_build", None)
                if build:
                    headers["X-NetGuard-Build"] = build["build_id"]
            await send(message)

        await self.app(scope, receive, protected_send if scope["type"] == "http" else send)
