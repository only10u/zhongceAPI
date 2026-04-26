"""在线检测 UI：评分、检查项（与 GET /v1/models 子串探测量一致；深度项标记为未执行）。"""

from __future__ import annotations

from typing import Any

from relay_probe.model_catalog import TRACKED_MODELS
from relay_probe.probe import ProbeResult


def build_report_ui(
    res: ProbeResult,
    matches: dict[str, bool],
    primary_slug: str,
    tr: dict[str, Any],
) -> dict[str, Any]:
    slugs = [m["slug"] for m in TRACKED_MODELS]
    http_ok = res.http_status is not None and 200 <= int(res.http_status) < 300
    primary_ok = bool(matches.get(primary_slug))
    three_hits = sum(1 for s in slugs if matches.get(s))
    lat_ok = res.latency_ms is not None

    score_pct = int(
        round(
            100
            * (
                0.5 * (1.0 if primary_ok else 0.0)
                + 0.3 * (three_hits / max(1, len(slugs)))
                + 0.2 * (1.0 if http_ok else 0.0)
            )
        )
    )
    score_pct = max(0, min(100, score_pct))

    if not http_ok:
        headline_zh = (
            f"请求未成功 (HTTP {res.http_status})"
            if res.http_status is not None
            else (res.error or "请求失败")
        )[:64]
        headline_en = (
            f"Request failed (HTTP {res.http_status})"
            if res.http_status is not None
            else "Request failed"
        )[:80]
    elif primary_ok:
        headline_zh = "主评线已命中"
        headline_en = "Primary line matched"
    else:
        headline_zh = "未达主评"
        headline_en = "Primary line not matched"

    def _st(ok: bool | None) -> str:
        if ok is None:
            return "skip"
        return "pass" if ok else "fail"

    lines_state = "pass" if three_hits >= len(slugs) else (
        "warn" if three_hits > 0 else "fail"
    )

    checklist: list[dict[str, Any]] = [
        {
            "id": "http",
            "state": _st(http_ok),
            "text_zh": "GET /v1/models 可访问（HTTP 2xx）",
            "text_en": "GET /v1/models returns HTTP 2xx",
        },
        {
            "id": "primary",
            "state": _st(primary_ok),
            "text_zh": f"主评线「{tr.get('name_zh', '')}」在返回中可匹配子串",
            "text_en": f"Primary line substring present ({primary_slug})",
        },
        {
            "id": "lines3",
            "state": lines_state,
            "text_zh": f"三线目标在目录中匹配数 {three_hits}/{len(slugs)}",
            "text_en": f"Three tracked lines matched: {three_hits}/{len(slugs)}",
        },
        {
            "id": "latency",
            "state": _st(lat_ok),
            "text_zh": "可计量首包延迟（目录请求）",
            "text_en": "Latency available (models listing)",
        },
        {
            "id": "deep",
            "state": "skip",
            "text_zh": "身份/签名/知识/多轮对话等深度项",
            "text_en": "Deep checks (not run; no chat request)",
        },
    ]

    card = tr.get("card_id", "")
    mt = tr.get("match")
    if isinstance(mt, (tuple, list)) and mt:
        ex_match = "、".join(str(x) for x in list(mt)[:3])
    else:
        ex_match = card or ""

    return {
        "score_percent": score_pct,
        "headline_zh": headline_zh,
        "headline_en": headline_en,
        "checklist": checklist,
        "disclaimer": {
            "primary_name_zh": tr.get("name_zh", ""),
            "primary_name_en": tr.get("name_en", ""),
            "primary_slug": primary_slug,
            "primary_card_id": card,
            "match_hint": ex_match,
        },
    }
