"""日 PV 写入与查询（UTC 按日）。"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy.orm import Session

from relay_probe.models import TrafficDay


def _today_utc() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()


def bump_page_view(db: Session) -> None:
    """当日 PV +1（幂等由调用方控制频率）。"""
    d = _today_utc()
    row = db.query(TrafficDay).filter(TrafficDay.day == d).one_or_none()
    if row is None:
        db.add(TrafficDay(day=d, page_views=1))
    else:
        row.page_views = int(row.page_views or 0) + 1
    db.commit()


def list_daily_series(db: Session, num_days: int = 30) -> list[dict[str, Any]]:
    """含首尾共 num_days 天；无记录补 0。"""
    n = max(1, min(int(num_days), 366))
    end = _today_utc()
    start = end - dt.timedelta(days=n - 1)
    rows = (
        db.query(TrafficDay)
        .filter(TrafficDay.day >= start, TrafficDay.day <= end)
        .order_by(TrafficDay.day)
        .all()
    )
    by_d = {r.day: int(r.page_views or 0) for r in rows}
    out: list[dict[str, Any]] = []
    cur = start
    while cur <= end:
        out.append({"day": cur.isoformat(), "page_views": by_d.get(cur, 0)})
        cur += dt.timedelta(days=1)
    return out
