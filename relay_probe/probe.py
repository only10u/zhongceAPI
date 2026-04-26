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


def result_to_dict(r: ProbeResult, include_body: bool = False) -> dict[str, Any]:
    d = asdict(r)
    if not include_body:
        d.pop("body_text", None)
    return d
