"""开放兼容网关 /v1/models 列表中可匹配的模型标记（子串不区分大小写）。

- **TRACKED_MODELS**：全站排行 / 定时探测入库 / 矩阵仅统计此三线。
- **HOME_DETECTOR_EXTRA_MODELS**：仅首页「在线检测」可选的附加线（不计入排行持久化三条之外的分表）。
"""

from __future__ import annotations

from typing import Any

# 排行、后台分线、定时探测 ModelProbeSample 只认此三线
TRACKED_MODELS: list[dict[str, Any]] = [
    {
        "slug": "opus-47",
        "name_zh": "Opus 4.7",
        "name_en": "Opus 4.7",
        "card_id": "claude-opus-4-7",
        "badge": "",
        "match": ("opus-4-7", "claude-opus-4-7", "4-7-202505", "4.7-2025"),
    },
    {
        "slug": "opus-46",
        "name_zh": "Opus 4.6",
        "name_en": "Opus 4.6",
        "card_id": "claude-opus-4-6",
        "badge": "",
        "match": ("opus-4-6", "claude-opus-4-6", "4-6-2025"),
    },
    {
        "slug": "sonnet-46",
        "name_zh": "Sonnet 4.6",
        "name_en": "Sonnet 4.6",
        "card_id": "claude-sonnet-4-6",
        "badge": "",
        "match": ("sonnet-4-6", "claude-sonnet-4-6", "claude-sonnet-4"),
    },
]

# 仅首页在线检测模块展示与匹配（试探测 JSON），不入库为第四条「全站分榜」
HOME_DETECTOR_EXTRA_MODELS: list[dict[str, Any]] = [
    {
        "slug": "gpt-55",
        "name_zh": "GPT 5.5",
        "name_en": "GPT 5.5",
        "card_id": "gpt-5.5",
        "badge": "new",
        "match": ("gpt-5.5", "gpt-5-5", "gpt5.5", "gpt_5.5"),
    },
    {
        "slug": "gpt-54",
        "name_zh": "GPT 5.4",
        "name_en": "GPT 5.4",
        "card_id": "gpt-5.4",
        "badge": "new",
        "match": ("gpt-5.4", "gpt-5-4", "gpt5.4", "gpt_5.4"),
    },
    {
        "slug": "gemini-31-pro",
        "name_zh": "Gemini 3.1 Pro",
        "name_en": "Gemini 3.1 Pro",
        "card_id": "gemini-3.1-pro",
        "badge": "new",
        "match": (
            "gemini-3.1-pro",
            "gemini-3.1",
            "gemini3.1-pro",
            "gemini-3-pro",
        ),
    },
]


def home_detector_models() -> list[dict[str, Any]]:
    """首页在线检测：三线 + 附加三线，共 6 个可选目标。"""
    return [*TRACKED_MODELS, *HOME_DETECTOR_EXTRA_MODELS]


def inclusion_checkbox_slugs() -> set[str]:
    return {m["slug"] for m in home_detector_models()}


def model_ids_from_models_response(body: str) -> str:
    """从 /v1/models 原始 JSON 文本中粗略提取可匹配的 id 拼接串（小写）。"""
    t = (body or "").lower()
    return t


def match_models(
    body_lower_blob: str,
    *,
    scope: str = "background",
) -> dict[str, bool]:
    """
    scope:
      - background: 仅三线，与 ModelProbeSample 入库一致
      - home_try: 首页试探测，六线全部匹配用于展示
    """
    models = (
        home_detector_models() if scope == "home_try" else TRACKED_MODELS
    )
    out: dict[str, bool] = {}
    for m in models:
        slug = m["slug"]
        found = any(tok in body_lower_blob for tok in m["match"])
        out[slug] = found
    return out


def get_tracked_by_slug(slug: str) -> dict[str, Any] | None:
    """排行用三线。"""
    for m in TRACKED_MODELS:
        if m["slug"] == slug:
            return m
    return None


def get_home_probe_model_by_slug(slug: str) -> dict[str, Any] | None:
    """首页试探测可选线（含附加）。"""
    for m in home_detector_models():
        if m["slug"] == slug:
            return m
    return None
