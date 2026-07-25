#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AuditAI Busan — 정적 파일 + AI 상담 프록시 (stdlib만 사용)

보안 원칙
- API 키는 .env 에만 두고 브라우저에 노출하지 않음
- LLM은 '판정'이 아니라 규칙엔진·지침 발췌의 '해설'만 수행
- 제공된 근거 밖의 조항·금액을 만들어 내지 않도록 시스템 프롬프트 고정
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

SYSTEM_PROMPT = """당신은 공공기관 예산 집행 상담의 '해설 보조'입니다.
절대 규칙:
1. 최종 가능/불가 판정은 하지 마세요. 입력의 RULE_VERDICT 를 그대로 존중하세요.
2. 제공된 RULE_ENGINE, GUIDE_EXCERPTS, TACIT, KB_CITES 에 없는 법령 조문·한도 금액·예외를 만들어 내지 마세요.
3. 근거가 부족하면 "제공된 자료만으로는 판단할 수 없습니다. 담당 부서·원문 대조가 필요합니다."라고 말하세요.
4. 답변은 한국어. 참고용임을 명시하세요.
5. 출력은 반드시 아래 JSON 한 개만 (마크다운·코드펜스 금지):
{
  "summary": "2~4문장 요약 (RULE_VERDICT 존중)",
  "explain": "담당자가 이해하기 쉬운 해설",
  "checklist": ["확인·준비 항목"],
  "citations": [{"source":"문서명 또는 규정명","quote":"제공된 근거에서 인용한 짧은 구절"}],
  "gaps": ["자료에 없어 확인이 필요한 점"],
  "disclaimer": "참고용이며 최종 판단은 담당 부서"
}
citations 의 quote 는 반드시 입력 근거에 실제로 존재하는 문구만 쓰세요. 없으면 citations 는 빈 배열.
"""

MAIL_SYSTEM_PROMPT = """당신은 공공기관 예산·증빙 요청 메일을 '다시 써서' 다듬는 보조입니다.
절대 규칙:
1. 입력 FACTS에 없는 서류명·금액·한도·법령·기한을 새로 만들지 마세요.
2. followup=true 이면: missing 목록의 서류만 추가 제출을 요청하세요. 받은 서류(received)·전체 목록·문의 요지를 본문에 다시 나열하지 마세요.
3. followup=false 이면: all/missing 목록 항목을 빼거나 바꾸지 마세요(표기만 자연스럽게).
4. 과장·압박·비난·법적 단정 표현 금지. 정중하고 짧은 업무 메일.
5. 한국어. 서명은 입력에 있으면 유지, 없으면 '예산 담당'.
6. 반드시 draftBody와 다른 문장으로 다시 쓰세요. 그대로 복사 금지.
   - 인사·요청 이유·서류 목록·감사 인사 순으로 읽기 쉽게
   - 딱딱한 관용구를 부드러운 업무체로
   - 서류 목록은 번호 목록으로 유지(이름 변경 금지)
7. 출력은 JSON 한 개만 (마크다운·코드펜스 금지):
{"subject":"메일 제목","body":"메일 본문 전체"}
"""


def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    # Windows 메모장 UTF-8 BOM / 공백·따옴표 대응
    text = path.read_text(encoding="utf-8-sig")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        key = k.strip().lstrip("\ufeff")
        val = v.strip().strip('"').strip("'")
        # 키=값 뒤 인라인 주석 제거는 하지 않음(키에 # 포함 가능)
        if key:
            env[key] = val
    return env


def apply_env(force: bool = False) -> None:
    """force=True 이면 .env 값을 OS 환경변수에 덮어씀(재시작 없이 키 갱신)."""
    loaded = load_env(ENV_PATH)
    for k, v in loaded.items():
        if force or k not in os.environ or not str(os.environ.get(k) or "").strip():
            os.environ[k] = v
    return


ENV = load_env(ENV_PATH)
apply_env(force=False)


def env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name, str(default)).strip().lower()
    return v in ("1", "true", "yes", "on", "y")


def ai_ready() -> dict:
    apply_env(force=True)  # 매 요청마다 .env 다시 읽기
    key = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    enabled = env_bool("AI_ENABLED", True)
    return {
        "ok": True,
        "ai": enabled and key,
        "aiEnabled": enabled,
        "hasKey": key,
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "mode": "grounded-explain-only",
        "envFile": str(ENV_PATH),
        "envExists": ENV_PATH.exists(),
    }


def clip(s, n: int) -> str:
    s = "" if s is None else str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def _norm_mail(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").strip())


def build_user_payload(data: dict) -> str:
    """클라이언트가 보낸 근거만 정리해 모델에 전달 (프롬프트 인젝션 완화)."""
    situation = clip(data.get("situation"), 2500)
    rule = data.get("rule") or {}
    guides = data.get("guides") or []
    tacit = data.get("tacit") or []
    kb = data.get("kb") or []
    need = data.get("need") or []
    contract = data.get("contract")
    ambiguity = data.get("ambiguity")

    guide_lines = []
    for i, g in enumerate(guides[:8], 1):
        name = clip(g.get("name"), 120)
        chunk = clip(g.get("chunk"), 900)
        guide_lines.append(f"[{i}] {name}\n{chunk}")

    parts = [
        "SITUATION:\n" + situation,
        "RULE_VERDICT:\n" + clip(rule.get("verdict"), 80),
        "RULE_ENGINE:\n" + clip(json.dumps(rule, ensure_ascii=False), 4000),
        "NEED_DOCS:\n" + clip("\n".join(f"- {x}" for x in need[:40]), 2000),
        "GUIDE_EXCERPTS:\n" + (clip("\n\n".join(guide_lines), 7000) or "(없음)"),
        "TACIT:\n" + (clip("\n".join(f"- {x}" for x in tacit[:20]), 1500) or "(없음)"),
        "KB_CITES:\n" + (clip("\n".join(f"- {x}" for x in kb[:30]), 2000) or "(없음)"),
    ]
    tacit_recs = data.get("tacitRecords") or []
    if tacit_recs:
        lines = []
        for i, t in enumerate(tacit_recs[:8], 1):
            if not isinstance(t, dict):
                continue
            lines.append(
                f"[{i}] 사업={clip(t.get('prj'),80)} / 비목={clip(t.get('cat'),80)}\n"
                f"상황: {clip(t.get('situation'),400)}\n"
                f"요령: {clip(t.get('exception'),400)}\n"
                f"제외서류: {clip(', '.join(t.get('skipDocs') or []),200)}\n"
                f"추가서류: {clip(', '.join(t.get('addDocs') or []),200)}"
            )
        parts.insert(
            5,
            "TACIT_RECORDS (동일 사업 상담 데이터 — 판정 변경 금지, 요령·서류만 참고):\n"
            + clip("\n\n".join(lines), 3500),
        )
    project = clip(data.get("project"), 120)
    if project:
        parts.insert(1, "PROJECT:\n" + project)
    if contract:
        parts.append("CONTRACT:\n" + clip(json.dumps(contract, ensure_ascii=False), 1200))
    if ambiguity:
        parts.append("AMBIGUITY:\n" + clip(json.dumps(ambiguity, ensure_ascii=False), 1500))
    parts.append(
        "지시: 위 근거만으로 JSON을 작성하세요. RULE_VERDICT를 바꾸지 마세요. "
        "근거에 없는 조문·금액을 쓰지 마세요."
    )
    return "\n\n".join(parts)


def build_mail_payload(data: dict) -> str:
    facts = {
        "followup": bool(data.get("followup")),
        "caseId": clip(data.get("caseId"), 40),
        "project": clip(data.get("project"), 120),
        "group": clip(data.get("group"), 80),
        "cat": clip(data.get("cat"), 80),
        "amount": data.get("amount"),
        "contractMode": clip(data.get("contractMode"), 200),
        "query": clip(data.get("query"), 800),
        "received": [clip(x, 120) for x in (data.get("received") or [])[:40]],
        "missing": [clip(x, 120) for x in (data.get("missing") or [])[:40]],
        "all": [clip(x, 120) for x in (data.get("all") or [])[:40]],
        "forms": [clip(x, 160) for x in (data.get("forms") or [])[:30]],
        "round": data.get("round") or 1,
        "draftSubject": clip(data.get("draftSubject"), 200),
        "draftBody": clip(data.get("draftBody"), 5000),
        "note": clip(data.get("note"), 500),
    }
    return (
        "FACTS (이 내용만 사용, 없는 사실 금지):\n"
        + json.dumps(facts, ensure_ascii=False, indent=2)
        + "\n\n지시: draftBody를 그대로 복사하지 말고, 같은 사실로 더 자연스러운 업무 메일 JSON"
        "(subject, body)을 새로 작성하세요. 서류 목록 항목명은 변경하지 마세요."
    )


def call_openai(
    user_text: str,
    *,
    system: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> dict:
    apply_env(force=True)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY 가 .env 에 없습니다. "
            f"파일 위치: {ENV_PATH}"
        )
    if not env_bool("AI_ENABLED", True):
        raise RuntimeError("AI_ENABLED=false 입니다.")

    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    if temperature is None:
        try:
            temperature = float(os.environ.get("AI_TEMPERATURE", "0"))
        except ValueError:
            temperature = 0.0
    try:
        default_max = int(os.environ.get("AI_MAX_TOKENS", "900"))
    except ValueError:
        default_max = 900
    tokens = max_tokens if max_tokens is not None else default_max

    body = {
        "model": model,
        "temperature": temperature,
        "max_tokens": tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system or SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    }
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"LLM HTTP {e.code}: {detail}") from e

    content = (
        ((raw.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    ).strip()
    if not content:
        raise RuntimeError("LLM 응답이 비어 있습니다.")

    # 혹시 모델이 코드펜스를 붙인 경우 제거
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {
            "summary": content[:500],
            "explain": content,
            "checklist": [],
            "citations": [],
            "gaps": ["JSON 파싱 실패 — 원문만 표시"],
            "disclaimer": "참고용이며 최종 판단은 담당 부서",
            "subject": "",
            "body": content,
        }
    if not isinstance(parsed, dict):
        raise RuntimeError("LLM JSON 형식이 올바르지 않습니다.")
    return {"ok": True, "model": model, "parsed": parsed}


def format_counsel_result(parsed: dict, model: str) -> dict:
    return {
        "ok": True,
        "model": model,
        "result": {
            "summary": clip(parsed.get("summary"), 800),
            "explain": clip(parsed.get("explain"), 4000),
            "checklist": [clip(x, 300) for x in (parsed.get("checklist") or [])[:12]],
            "citations": [
                {
                    "source": clip(c.get("source"), 200),
                    "quote": clip(c.get("quote"), 400),
                }
                for c in (parsed.get("citations") or [])[:10]
                if isinstance(c, dict)
            ],
            "gaps": [clip(x, 300) for x in (parsed.get("gaps") or [])[:10]],
            "disclaimer": clip(
                parsed.get("disclaimer")
                or "참고용이며 최종 판단은 담당 부서",
                400,
            ),
        },
    }


def format_mail_result(parsed: dict, model: str, data: dict | None = None) -> dict:
    subject = clip(parsed.get("subject"), 200).strip()
    body = clip(parsed.get("body"), 8000).strip()
    if not body:
        raise RuntimeError("메일 본문이 비어 있습니다.")
    # 모델이 서류명을 빼먹으면 목록을 덧붙여 사실 보존
    data = data or {}
    missing = [str(x).strip() for x in (data.get("missing") or []) if str(x).strip()]
    if missing:
        absent = [d for d in missing if d not in body]
        if absent:
            lines = "\n".join(f"{i}. {d}" for i, d in enumerate(missing, 1))
            body = (
                body.rstrip()
                + "\n\n■ 추가 제출 부탁 ("
                + str(len(missing))
                + "종) — 서류명 유지\n"
                + lines
                + "\n"
            )
    return {
        "ok": True,
        "model": model,
        "result": {
            "subject": subject or "[증빙요청] 서류 안내",
            "body": body,
        },
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _cors(self):
        origin = self.headers.get("Origin", "")
        allow = os.environ.get("ALLOWED_ORIGIN", "").strip()
        if allow:
            self.send_header("Access-Control-Allow-Origin", allow)
        elif origin.startswith("http://127.0.0.1") or origin.startswith(
            "http://localhost"
        ):
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code: int, obj: dict):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/health":
            self._json(200, ai_ready())
            return
        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path not in ("/api/counsel", "/api/mail"):
            self._json(404, {"ok": False, "error": "not found"})
            return
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
        # 클라이언트가 system 메시지를 넣어도 무시
        data.pop("system", None)
        data.pop("messages", None)
        try:
            if path == "/api/mail" or data.get("task") == "mail":
                # 메일은 문장 다듬기가 목적이라 온도를 조금 올림 (상담 해설은 기본 온도 유지)
                try:
                    mail_temp = float(os.environ.get("AI_MAIL_TEMPERATURE", "0.45"))
                except ValueError:
                    mail_temp = 0.45
                raw = call_openai(
                    build_mail_payload(data),
                    system=MAIL_SYSTEM_PROMPT,
                    max_tokens=1200,
                    temperature=mail_temp,
                )
                out = format_mail_result(raw["parsed"], raw["model"], data)
                # 모델이 초안을 그대로 반환하면 한 번 더 강하게 재시도
                draft = str(data.get("draftBody") or "").strip()
                body = str((out.get("result") or {}).get("body") or "").strip()
                if draft and body and _norm_mail(draft) == _norm_mail(body):
                    raw2 = call_openai(
                        build_mail_payload(data)
                        + "\n\n추가: 이전 출력이 draft와 동일했습니다. "
                        "인사말·본문 서술·맺음말을 분명히 바꿔 다시 쓰세요. 서류명만 유지.",
                        system=MAIL_SYSTEM_PROMPT,
                        max_tokens=1200,
                        temperature=min(0.75, mail_temp + 0.3),
                    )
                    out = format_mail_result(raw2["parsed"], raw2["model"], data)
            else:
                raw = call_openai(build_user_payload(data))
                out = format_counsel_result(raw["parsed"], raw["model"])
            self._json(200, out)
        except Exception as e:
            self._json(502, {"ok": False, "error": str(e)})

    def log_message(self, fmt, *args):
        sys.stderr.write("[AuditAI] " + (fmt % args) + "\n")


def main():
    apply_env(force=True)
    try:
        port = int(os.environ.get("PORT", "8765"))
    except ValueError:
        port = 8765
    os.chdir(ROOT)
    status = ai_ready()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print()
    print("  AuditAI Busan  local server")
    print(f"  http://127.0.0.1:{port}/index.html")
    print(f"  .env       : {ENV_PATH}")
    print(f"  .env 존재  : {status['envExists']}")
    print(f"  API 키     : {'인식됨' if status['hasKey'] else '없음 — .env 에 OPENAI_API_KEY= 확인'}")
    print(f"  AI counsel : {'ON' if status['ai'] else 'OFF'}")
    print(f"  model      : {status['model']}")
    print("  ※ index.html 을 더블클릭(file://)하면 AI가 안 됩니다. 반드시 이 서버 URL로 여세요.")
    print("  종료: Ctrl+C")
    print()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n종료")


if __name__ == "__main__":
    main()
