"""Deterministic browser asset types without changing the process MIME registry."""

import os
from pathlib import Path

from starlette.responses import FileResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

_BROWSER_TYPES = {".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css"}


class AppStaticFiles(StaticFiles):
    def file_response(
        self,
        full_path: str | os.PathLike[str],
        stat_result: os.stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        # Keep Starlette's path checks, validators, HEAD and byte-range handling.
        response = super().file_response(full_path, stat_result, scope, status_code)
        media_type = _BROWSER_TYPES.get(Path(full_path).suffix.lower())
        if media_type is not None and isinstance(response, FileResponse):
            response.media_type = media_type  # Also used inside multipart byte ranges.
            response.headers["content-type"] = f"{media_type}; charset=utf-8"
        return response
