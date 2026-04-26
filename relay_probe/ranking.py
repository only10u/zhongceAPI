import datetime as dt
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from relay_probe.config import Settings
from relay_probe.models import ProbeSample, Relay

settings = Settings()


def window_start_utc(hours: int) -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)


def delete_old_samples(db: Session) -> int:
    """返回删除行数。"""
    before = dt.datetime.now(dt.timezone.utc) - dt.timedelta(
        days=settings.sample_retention_days
    )
    return (
        db.query(ProbeSample)
        .filter(ProbeSample.created_at < before)
        .delete(synchronize_session=False)
    )


def build_ranking_rows(db: Session, window_hours: int | None = None) -> list[dict[str, Any]]:
    h = window_hours if window_hours is not None else settings.ranking_window_hours
    since = window_start_utc(h)

    agg = select(
        ProbeSample.relay_id,
        func.count(ProbeSample.id).label("n"),
        func.coalesce(
            func.sum(case((ProbeSample.ok, 1), else_=0)), 0
        ).label("n_ok"),
        func.avg(
            case(
                (ProbeSample.ok, ProbeSample.latency_ms),
                else_=None,
            )
        ).label("avg_ok_latency_ms"),
    ).where(ProbeSample.created_at >= since)
    agg = agg.group_by(ProbeSample.relay_id)
    stat_map: dict[int, dict[str, Any]] = {}
    for row in db.execute(agg).all():
        rid = int(row.relay_id)
        n = int(row.n)
        n_ok = int(row.n_ok)
        avg = row.avg_ok_latency_ms
        success_rate = (n_ok / n) if n else 0.0
        stat_map[rid] = {
            "samples_in_window": n,
            "ok_in_window": n_ok,
            "success_rate": round(success_rate, 6),
            "avg_latency_ms": round(float(avg), 2) if avg is not None else None,
        }

    relays = db.query(Relay).order_by(Relay.id).all()
    rows: list[dict[str, Any]] = []
    for r in relays:
        st = stat_map.get(
            r.id,
            {
                "samples_in_window": 0,
                "ok_in_window": 0,
                "success_rate": 0.0,
                "avg_latency_ms": None,
            },
        )
        last = (
            db.query(ProbeSample)
            .filter(ProbeSample.relay_id == r.id)
            .order_by(ProbeSample.created_at.desc())
            .first()
        )
        rows.append(
            {
                "relay_id": r.id,
                "name": r.name,
                "base_url": r.base_url,
                "enabled": r.enabled,
                "check_path": r.check_path,
                "samples_in_window": st["samples_in_window"],
                "ok_in_window": st["ok_in_window"],
                "success_rate": st["success_rate"],
                "avg_latency_ms": st["avg_latency_ms"],
                "last_check_at": last.created_at.isoformat() if last else None,
                "last_ok": last.ok if last else None,
                "last_latency_ms": last.latency_ms if last else None,
            }
        )

    def rank_key(d: dict[str, Any]) -> tuple:
        n = d["samples_in_window"]
        if n == 0:
            return (1, 0, "")
        sr = d["success_rate"]
        lat = d["avg_latency_ms"] if d["avg_latency_ms"] is not None else 1e9
        return (0, -sr, lat)

    rows.sort(key=rank_key)
    for i, d in enumerate(rows, start=1):
        d["rank"] = i
    return rows
