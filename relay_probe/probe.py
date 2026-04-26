import time
from dataclasses import asdict, dataclass
from typing import Any

import httpx

from relay_probe.config import Settings


@dataclass
class ProbeResult:
    ok: bool
    latency_ms: float | None
    http_status: int | None
    error: str | None
    body_preview: str | None


def run_probe(s: Settings) -> ProbeResult:
    if not s.relay_base_url:
        return ProbeResult(
            ok=False,
            latency_ms=None,
            http_status=None,
            error="RELAY_BASE_URL 未配置",
            body_preview=None,
        )

    headers: dict[str, str] = {}
    if s.relay_api_key:
        headers["Authorization"] = f"Bearer {s.relay_api_key}"

    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=s.http_timeout_sec) as client:
            r = client.get(s.check_url, headers=headers)
    except Exception as e:  # noqa: BLE001 — surface any transport error
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
    d = asdict(r)
    return d
