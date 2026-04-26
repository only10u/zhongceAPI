"""开放兼容网关 /v1/models 列表中可匹配的模型标记（子串不区分大小写）。"""

from typing import Any

# slug 与 API 中展示名（中英）；card_id 为卡片区底部展示的模型 ID 文案（与常见网关 id 一致）
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
    {
        "slug": "gpt-55",
        "name_zh": "GPT 5.5",
        "name_en": "GPT 5.5",
        "card_id": "gpt-5.5",
        "badge": "new",
        "match": (
            "gpt-5.5",
            "gpt-5-5",
            "gpt5.5",
            "gpt_5.5",
        ),
    },
    {
        "slug": "gpt-54",
        "name_zh": "GPT 5.4",
        "name_en": "GPT 5.4",
        "card_id": "gpt-5.4",
        "badge": "new",
        "match": (
            "gpt-5.4",
            "gpt-5-4",
            "gpt5.4",
            "gpt_5.4",
        ),
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
# 全站排行 / 首页 / 在线检测共用以上目标线（子串匹配 /v1/models 正文）


def model_ids_from_models_response(body: str) -> str:
    """从 /v1/models 原始 JSON 文本中粗略提取可匹配的 id 拼接串（小写）。"""
    t = (body or "").lower()
    return t


def match_models(body_lower_blob: str) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for m in TRACKED_MODELS:
        slug = m["slug"]
        found = any(tok in body_lower_blob for tok in m["match"])
        out[slug] = found
    return out


def get_tracked_by_slug(slug: str) -> dict[str, Any] | None:
    for m in TRACKED_MODELS:
        if m["slug"] == slug:
            return m
    return None
