# Vercel serverless: POST /api/counsel
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import (  # noqa: E402
    apply_env,
    build_user_payload,
    call_openai,
    format_counsel_result,
)


class handler(BaseHTTPRequestHandler):
    def _json(self, code: int, obj: dict):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        apply_env(force=True)
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        if n <= 0 or n > 400_000:
            self._json(400, {"ok": False, "error": "본문 크기 오류"})
            return
        try:
            data = json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            self._json(400, {"ok": False, "error": "JSON 파싱 실패"})
            return
        if not isinstance(data, dict):
            self._json(400, {"ok": False, "error": "본문은 객체여야 합니다"})
            return
        data.pop("system", None)
        data.pop("messages", None)
        try:
            raw = call_openai(build_user_payload(data))
            self._json(200, format_counsel_result(raw["parsed"], raw["model"]))
        except Exception as e:
            self._json(502, {"ok": False, "error": str(e)})

    def log_message(self, fmt, *args):
        return
