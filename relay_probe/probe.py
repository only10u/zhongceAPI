import json
import time
from dataclasses import asdict, dataclass
from typing import Any

import httpx

from relay_probe.config import check_url_for


@dataclass
class ProbeResult:
    ok: bool
    latency_ms: float | None
    http_status: int | None
    error: str | None
    body_preview: str | None
    # 供 /v1/models 子串匹配，过大时截断
    body_text: str | None = None


@dataclass
class ChatUsageResult:
    """一次 POST /v1/chat/completions 的用量与延迟（非流式）。"""

    ok: bool
    latency_ms: float | None
    http_status: int | None
    error: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    cache_read: int | None
    cache_write: int | None
    tokens_per_sec: float | None
    model_id_used: str | None


def run_probe(
    base_url: str,
    check_path: str,
    http_timeout_sec: float,
    api_key: str | None = None,
) -> ProbeResult:
    b = (base_url or "").strip()
    if not b:
        return ProbeResult(
            ok=False,
            latency_ms=None,
            http_status=None,
            error="base_url 为空",
            body_preview=None,
        )
    path = (check_path or "/v1/models").strip() or "/v1/models"
    url = check_url_for(b, path)
    headers: dict[str, str] = {}
    if api_key and api_key.strip():
        headers["Authorization"] = f"Bearer {api_key.strip()}"

    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=http_timeout_sec) as client:
            r = client.get(url, headers=headers)
    except Exception as e:  # noqa: BLE001
        return ProbeResult(
            ok=False,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            http_status=None,
            error=str(e),
            body_preview=None,
        )

    elapsed = round((time.perf_counter() - t0) * 1000, 2)
    full = r.text or ""
    preview = (full)[:2000]
    text_cap = 400_000
    body_blob = full[:text_cap] if full else None
    ok = 200 <= r.status_code < 300
    return ProbeResult(
        ok=ok,
        latency_ms=elapsed,
        http_status=r.status_code,
        error=None if ok else f"HTTP {r.status_code}",
        body_preview=preview or None,
        body_text=body_blob if ok else None,
    )


def _coerce_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        n = int(v)
    except (TypeError, ValueError):
        return None
    return n if n >= 0 else None


def _parse_usage_from_json(data: Any) -> tuple[int | None, int | None, int | None, int | None, int | None]:
    """
    解析 OpenAI 兼容 completion 的 usage 字段，兼容常见网关/Anthropic 代理字段名。
    返回: prompt, completion, total, cache_read, cache_write
    """
    if not isinstance(data, dict):
        return (None, None, None, None, None)
    u = data.get("usage")
    if not isinstance(u, dict):
        u = {}
    prompt = _coerce_int(
        u.get("prompt_tokens")
    ) or _coerce_int(u.get("input_tokens"))
    completion = _coerce_int(
        u.get("completion_tokens")
    ) or _coerce_int(u.get("output_tokens"))
    total = _coerce_int(u.get("total_tokens"))
    if total is None and (prompt is not None or completion is not None):
        total = (prompt or 0) + (completion or 0) or None
    cread: int | None = None
    cwrite: int | None = None
    ptd = u.get("prompt_tokens_details")
    if isinstance(ptd, dict):
        cread = _coerce_int(ptd.get("cached_tokens")) or cread
    cread = cread or _coerce_int(u.get("cache_read_input_tokens")) or _coerce_int(
        u.get("cached_input_tokens")
    )
    cwrite = _coerce_int(u.get("cache_creation_input_tokens")) or cwrite
    return (prompt, completion, total, cread, cwrite)


def run_chat_completions_usage(
    base_url: str,
    model_id: str,
    http_timeout_sec: float,
    api_key: str,
) -> ChatUsageResult:
    """
    非流式 POST /v1/chat/completions，从返回体解析 usage 与首包时延（整段请求时延）。
    """
    b = (base_url or "").strip()
    key = (api_key or "").strip()
    if not b or not key:
        return ChatUsageResult(
            False,
            None,
            None,
            "缺少 base_url 或 API Key",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
    mid = (model_id or "").strip() or "gpt-4o-mini"
    url = check_url_for(b, "/v1/chat/completions")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": mid,
        "messages": [{"role": "user", "content": "ok"}],
        "max_tokens": 24,
        "stream": False,
    }
    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=http_timeout_sec) as client:
            r = client.post(url, headers=headers, json=body)
    except Exception as e:  # noqa: BLE001
        return ChatUsageResult(
            False,
            round((time.perf_counter() - t0) * 1000, 2),
            None,
            str(e)[:200],
            None,
            None,
            None,
            None,
            None,
            None,
            mid,
        )
    elapsed = round((time.perf_counter() - t0) * 1000, 2)
    sc = r.status_code
    ok = 200 <= int(sc) < 300
    data: Any = None
    try:
        if r.text:
            data = json.loads(r.text)
    except json.JSONDecodeError:
        data = None
    err_msg: str | None = None
    if not ok:
        if isinstance(data, dict) and data.get("error"):
            err = data["error"]
            if isinstance(err, dict) and err.get("message"):
                err_msg = str(err.get("message"))[:200]
            else:
                err_msg = str(err)[:200]
        else:
            err_msg = (r.text or "")[:200] or f"HTTP {sc}"
    prompt, completion, total, cread, cwrite = (None, None, None, None, None)
    if ok and data is not None:
        prompt, completion, total, cread, cwrite = _parse_usage_from_json(data)
        if not any(
            x is not None
            for x in (prompt, completion, total, cread, cwrite)
        ):
            err_msg = err_msg or "HTTP 2xx 但未解析到 usage 字段"
    tok_ps: float | None = None
    comp_n = completion if completion is not None else 0
    if ok and comp_n and comp_n > 0 and elapsed and elapsed > 0:
        tok_ps = round(comp_n / (elapsed / 1000.0), 2)
    return ChatUsageResult(
        ok,
        elapsed,
        int(sc) if sc is not None else None,
        err_msg,
        prompt,
        completion,
        total,
        cread,
        cwrite,
        tok_ps,
        mid,
    )


def chat_usage_to_dict(c: ChatUsageResult) -> dict[str, Any]:
    d = asdict(c)
    d["usage_parsed"] = any(
        x is not None
        for x in (
            c.prompt_tokens,
            c.completion_tokens,
            c.total_tokens,
            c.cache_read,
            c.cache_write,
        )
    )
    return d


def result_to_dict(r: ProbeResult, include_body: bool = False) -> dict[str, Any]:
    d = asdict(r)
    if not include_body:
        d.pop("body_text", None)
    return d
