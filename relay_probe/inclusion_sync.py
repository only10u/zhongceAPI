"""将中转站（relays）同步为收录表（inclusion_requests），供后台与公开展示共用。"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from relay_probe.model_catalog import TRACKED_MODELS
from relay_probe.models import InclusionRequest, Relay
from relay_probe.relay_rank_shelf import parse_rank_map_json


def default_supported_models_json_for_relay(r: Relay) -> str:
    rm = parse_rank_map_json(r.rank_models_json)
    slugs = [m["slug"] for m in TRACKED_MODELS if rm.get(m["slug"], True)]
    return json.dumps(slugs, ensure_ascii=False)


def _row_from_relay(r: Relay) -> InclusionRequest:
    fd = r.created_at.date() if getattr(r, "created_at", None) else None
    return InclusionRequest(
        relay_id=int(r.id),
        site_name=(r.name or "").strip() or "未命名站点",
        site_url=(r.base_url or "").strip() or "https://example.invalid",
        founded_date=fd,
        signup_url=None,
        contact_person=None,
        contact=None,
        suggested_group=(r.group_name or "").strip() or None,
        remark=None,
        supported_models_json=default_supported_models_json_for_relay(r),
        probe_account=None,
        probe_password=None,
        status="approved",
    )


def sync_all_relays_to_inclusion(db: Session) -> dict[str, Any]:
    """为每个尚无 relay_id 绑定的中转站插入一条「已通过」收录记录；不覆盖已有绑定。"""
    relays = db.query(Relay).order_by(Relay.id).all()
    bound = {
        int(x)
        for x, in db.query(InclusionRequest.relay_id)
        .filter(InclusionRequest.relay_id.is_not(None))
        .all()
        if x is not None
    }
    created = 0
    for r in relays:
        if int(r.id) in bound:
            continue
        db.add(_row_from_relay(r))
        created += 1
        bound.add(int(r.id))
    if created:
        db.commit()
    return {
        "created": created,
        "skipped": len(relays) - created,
        "total_relays": len(relays),
    }


def ensure_inclusion_for_new_relay(db: Session, relay: Relay) -> None:
    """新建中转站后补一条收录（若尚无绑定）。"""
    ex = (
        db.query(InclusionRequest)
        .filter(InclusionRequest.relay_id == relay.id)
        .first()
    )
    if ex:
        return
    db.add(_row_from_relay(relay))
    db.commit()
