"""按模型线号聚合：在线率、平均延迟、运行状态。掺水率以人工 override 或占位 —— 。"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from relay_probe.config import Settings
from relay_probe.model_catalog import TRACKED_MODELS
from relay_probe.models import ModelProbeSample, Relay

settings = Settings()


def window_start_utc(hours: int) -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)


def build_per_model_table(
    db: Session, model_slug: str, window_hours: int
) -> list[dict[str, Any]]:
    since = window_start_utc(window_hours)
    n_ok = func.coalesce(
        func.sum(case((ModelProbeSample.present == True, 1), else_=0)), 0
    ).label("n_in")
    n_all = func.count(ModelProbeSample.id).label("n_all")
    avg_lat = func.avg(
        case(
            (ModelProbeSample.present == True, ModelProbeSample.latency_ms),
            else_=None,
        )
    ).label("avg_lat")

    stmt = (
        select(
            ModelProbeSample.relay_id,
            n_all,
            n_ok,
            avg_lat,
        )
        .where(
            ModelProbeSample.model_slug == model_slug,
            ModelProbeSample.created_at >= since,
        )
        .group_by(ModelProbeSample.relay_id)
    )
    stat: dict[int, dict[str, Any]] = {}
    for row in db.execute(stmt).all():
        rid = int(row.relay_id)
        n_in = int(row.n_in) if row.n_in is not None else 0
        n = int(row.n_all)
        ar = float(row.avg_lat) if row.avg_lat is not None else None
        online_rate = (n_in / n) if n else 0.0
        stat[rid] = {
            "online_rate": round(online_rate, 4),
            "avg_latency_ms": round(ar, 2) if ar is not None else None,
            "samples": n,
        }
    # last state
    relays = (
        db.query(Relay)
        .filter(Relay.enabled.is_(True))
        .order_by(Relay.id)
        .all()
    )
    out: list[dict[str, Any]] = []
    for r in relays:
        st = stat.get(
            r.id,
            {
                "online_rate": 0.0,
                "avg_latency_ms": None,
                "samples": 0,
            },
        )
        last = (
            db.query(ModelProbeSample)
            .filter(
                ModelProbeSample.relay_id == r.id,
                ModelProbeSample.model_slug == model_slug,
                ModelProbeSample.created_at >= since,
            )
            .order_by(ModelProbeSample.created_at.desc())
            .first()
        )
        if st["samples"] == 0 and last is None:
            run_st = "无数据"
            st_cls = "st-muted"
        elif last is not None:
            if last.present:
                run_st = "在线"
                st_cls = "st-ok"
            else:
                run_st = "未列此模型"
                st_cls = "st-warn"
        else:
            run_st = "无数据"
            st_cls = "st-muted"
        dilution = "—"
        if r.dilution_override is not None:
            dilution = f"{r.dilution_override:.0f}%"
        out.append(
            {
                "relay_id": r.id,
                "name": r.name,
                "base_url": r.base_url,
                "group": r.group_name or "—",
                "price": r.site_price or "—",
                "online_rate": st["online_rate"],
                "online_rate_pct": round(st["online_rate"] * 100, 1) if st["samples"] else "—",
                "dilution": dilution,
                "avg_latency_ms": st["avg_latency_ms"],
                "status": run_st,
                "status_class": st_cls,
            }
        )
    # 排序：在线率降序、延迟升
    def k(x: dict[str, Any]) -> tuple:
        orv = x["online_rate"] if x["online_rate"] is not None else 0.0
        latv = x["avg_latency_ms"] if x["avg_latency_ms"] is not None else 1e9
        return (-orv, latv, x["name"])

    out.sort(key=k)
    for i, row in enumerate(out, 1):
        row["rank"] = i
    return out


def build_full_dashboard(
    db: Session, window_hours: int | None = None
) -> dict[str, Any]:
    h = window_hours if window_hours is not None else settings.ranking_window_hours
    by_model: dict[str, list[dict[str, Any]]] = {}
    for m in TRACKED_MODELS:
        slug = m["slug"]
        by_model[slug] = build_per_model_table(db, slug, h)
    return {
        "window_hours": h,
        "models_meta": [
            {
                "slug": m["slug"],
                "name_zh": m["name_zh"],
                "name_en": m["name_en"],
            }
            for m in TRACKED_MODELS
        ],
        "by_model": by_model,
    }
