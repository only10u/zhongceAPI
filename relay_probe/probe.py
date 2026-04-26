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
    text = (r.text or "")[:2000]
    ok = 200 <= r.status_code < 300
    return ProbeResult(
        ok=ok,
        latency_ms=elapsed,
        http_status=r.status_code,
        error=None if ok else f"HTTP {r.status_code}",
        body_preview=text or None,
    )


def result_to_dict(r: ProbeResult) -> dict[str, Any]:
    return asdict(r)
