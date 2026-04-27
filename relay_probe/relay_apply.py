"""中转站更新字段：供 X-Admin-Token 与登录管理员 PATCH 复用。"""

from __future__ import annotations

from relay_probe.models import Relay
from relay_probe.relay_rank_shelf import default_rank_map, dumps_rank_map
from relay_probe.schemas import RelayUpdate


def apply_relay_update(r: Relay, body: RelayUpdate) -> None:
    d = body.model_dump(exclude_unset=True, exclude_none=False)
    if "name" in d and d["name"] is not None:
        r.name = d["name"].strip()
    if "base_url" in d and d["base_url"] is not None:
        r.base_url = d["base_url"].strip().rstrip("/")
    if "api_key" in d:
        v = d["api_key"]
        r.api_key = (v or "").strip() or None
    if "check_path" in d and d["check_path"] is not None:
        r.check_path = d["check_path"].strip() or "/v1/models"
    if "enabled" in d:
        r.enabled = bool(d["enabled"])
    if "rank_boost" in d:
        r.rank_boost = int(d["rank_boost"] or 0)
    if "group_name" in d:
        v = d["group_name"]
        r.group_name = (v or "").strip() or None
    if "site_price" in d:
        v = d["site_price"]
        r.site_price = (v or "").strip() or None
    if "pricing_input_usd" in d:
        v = d["pricing_input_usd"]
        r.pricing_input_usd = (v or "").strip() or None
    if "pricing_output_usd" in d:
        v = d["pricing_output_usd"]
        r.pricing_output_usd = (v or "").strip() or None
    if "price_sort_key" in d:
        r.price_sort_key = d["price_sort_key"]
    if "dilution_label" in d:
        v = d["dilution_label"]
        r.dilution_label = (v or "").strip() or None
    if "dilution_override" in d:
        r.dilution_override = d["dilution_override"]
    if "rank_models" in d and d["rank_models"] is not None:
        merged = default_rank_map()
        for k, v in d["rank_models"].items():
            if k in merged:
                merged[k] = bool(v)
        r.rank_models_json = dumps_rank_map(merged)
