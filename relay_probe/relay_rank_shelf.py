"""各中转在分榜中的「上架」：rank_models_json 为 JSON 对象，slug -> 是否参与该线排行展示。"""
from __future__ import annotations

import json
from typing import Any

from relay_probe.model_catalog import TRACKED_MODELS
from relay_probe.models import Relay


def relay_rank_enabled(r: Relay, slug: str) -> bool:
    raw = getattr(r, "rank_models_json", None)
    if raw is None or (isinstance(raw, str) and not str(raw).strip()):
        return True
    try:
        m: Any = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return True
    if not isinstance(m, dict):
        return True
    if slug not in m:
        return True
    return bool(m[slug])


def default_rank_map() -> dict[str, bool]:
    return {m["slug"]: True for m in TRACKED_MODELS}


def parse_rank_map_json(s: str | None) -> dict[str, bool]:
    out = default_rank_map()
    if not s or not str(s).strip():
        return out
    try:
        m = json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return out
    if not isinstance(m, dict):
        return out
    for k, v in m.items():
        if k in out:
            out[k] = bool(v)
    return out


def dumps_rank_map(d: dict[str, bool]) -> str:
    return json.dumps(d, ensure_ascii=False, separators=(",", ":"))
