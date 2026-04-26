"""开放兼容网关 /v1/models 列表中可匹配的模型标记（子串不区分大小写）。"""

from typing import Any

# slug 与 API 中展示名（中英）
TRACKED_MODELS: list[dict[str, Any]] = [
    {
        "slug": "opus-47",
        "name_zh": "Opus 4.7",
        "name_en": "Opus 4.7",
        "match": ("opus-4-7", "claude-opus-4-7", "4-7-202505", "4.7-2025"),
    },
    {
        "slug": "opus-46",
        "name_zh": "Opus 4.6",
        "name_en": "Opus 4.6",
        "match": ("opus-4-6", "claude-opus-4-6", "4-6-2025"),
    },
    {
        "slug": "sonnet-46",
        "name_zh": "Sonnet 4.6",
        "name_en": "Sonnet 4.6",
        "match": ("sonnet-4-6", "claude-sonnet-4-6", "claude-sonnet-4"),
    },
    {
        "slug": "gpt-5-5",
        "name_zh": "GPT 5.5",
        "name_en": "GPT 5.5",
        "match": ("gpt-5.5", "gpt-5-5", "gpt-5-5-2025", "5.5-2025"),
    },
    {
        "slug": "gpt-5-4",
        "name_zh": "GPT 5.4",
        "name_en": "GPT 5.4",
        "match": ("gpt-5.4", "gpt-5-4", "5.4-2025"),
    },
    {
        "slug": "gemini-3-1",
        "name_zh": "Gemini 3.1 Pro",
        "name_en": "Gemini 3.1 Pro",
        "match": (
            "gemini-3.1-pro",
            "gemini-3.1",
            "3.1-pro",
            "gemini-3-pro",
        ),
    },
]


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
