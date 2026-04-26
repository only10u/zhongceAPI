import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.orm import Session

from relay_probe import __version__
from relay_probe.config import Settings
from relay_probe.database import SessionLocal, get_db, init_db
from relay_probe.models import ProbeSample, Relay
from relay_probe.probesample_helper import add_model_samples_from_probe
from relay_probe.probe import ProbeResult, result_to_dict, run_probe
from relay_probe.ranking import build_ranking_rows, delete_old_samples
from relay_probe.schemas import Message, RelayCreate, RelayUpdate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("relay_probe")
settings = Settings()
_WARNED_INSECURE = False


def _admin_warned() -> None:
    global _WARNED_INSECURE
    if not settings.admin_token and not _WARNED_INSECURE:
        _WARNED_INSECURE = True
        log.warning(
            "未设置 ADMIN_TOKEN，写操作（增删改中转）对任意客户端开放；生产环境请设置强随机口令"
        )


def _verify_admin(x_admin_token: str | None) -> None:
    if not settings.admin_token:
        _admin_warned()
        return
    if (x_admin_token or "").strip() != settings.admin_token.strip():
        raise HTTPException(status_code=401, detail="需要有效的 X-Admin-Token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.check_interval_sec > 0:
        t = asyncio.create_task(_background_loop())
        try:
            yield
        finally:
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
    else:
        yield


async def _background_loop() -> None:
    while True:
        await asyncio.to_thread(_probe_all_sync)
        await asyncio.sleep(settings.check_interval_sec)


def _probe_all_sync() -> None:
    db = SessionLocal()
    try:
        removed = delete_old_samples(db)
        if removed:
            log.info("pruned old samples: %s", removed)
        relays = (
            db.query(Relay)
            .filter(Relay.enabled.is_(True))
            .order_by(Relay.id)
            .all()
        )
        for r in relays:
            res = run_probe(
                r.base_url,
                r.check_path,
                settings.http_timeout_sec,
                r.api_key,
            )
            db.add(
                ProbeSample(
                    relay_id=r.id,
                    ok=res.ok,
                    latency_ms=res.latency_ms,
                    http_status=res.http_status,
                    error=res.error,
                )
            )
            add_model_samples_from_probe(db, r.id, res)
            if res.ok:
                log.info("probe ok id=%s name=%s latency_ms=%s", r.id, r.name, res.latency_ms)
            else:
                log.warning(
                    "probe fail id=%s name=%s err=%s", r.id, r.name, res.error
                )
        delete_old_samples(db)
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        log.exception("background probe failed")
    finally:
        db.close()


def _probe_one_sync(relay_id: int) -> tuple[ProbeResult, str | None]:
    db = SessionLocal()
    try:
        r = db.query(Relay).filter(Relay.id == relay_id).one_or_none()
        if r is None:
            return (
                ProbeResult(
                    False, None, None, "relay 不存在", None, None
                ),
                None,
            )
        res = run_probe(
            r.base_url, r.check_path, settings.http_timeout_sec, r.api_key
        )
        sample = ProbeSample(
            relay_id=r.id,
            ok=res.ok,
            latency_ms=res.latency_ms,
            http_status=res.http_status,
            error=res.error,
        )
        db.add(sample)
        add_model_samples_from_probe(db, r.id, res)
        delete_old_samples(db)
        db.commit()
        t = (
            sample.created_at.isoformat()
            if sample.created_at
            else None
        )
        return res, t
    except Exception:  # noqa: BLE001
        db.rollback()
        log.exception("probe one failed relay_id=%s", relay_id)
        return (
            ProbeResult(False, None, None, "数据库写入失败", None, None),
            None,
        )
    finally:
        db.close()


app = FastAPI(
    title="中测",
    description="中转站 API 检测平台 — 多中转探测、统计与排名（海外检测节点）",
    version=__version__,
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.head("/health")
def health_head() -> Response:
    """供 curl -I / 监控 HEAD 探测，避免 405。"""
    return Response(status_code=200)


@app.get("/api/ranking")
def api_ranking(
    window_hours: int | None = None,
    db: Session = Depends(get_db),
) -> JSONResponse:
    h = window_hours if window_hours is not None else settings.ranking_window_hours
    if h < 1 or h > 168:
        raise HTTPException(400, detail="window_hours 应在 1–168 之间")
    rows = build_ranking_rows(db, window_hours=h)
    return JSONResponse(
        content={
            "version": __version__,
            "window_hours": h,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "rows": rows,
        }
    )


@app.get("/api/relays", response_model=list[dict[str, Any]])
def list_relays(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in db.query(Relay).order_by(Relay.id).all():
        d = r.to_public_dict()
        d["has_api_key"] = bool(r.api_key and r.api_key.strip())
        out.append(d)
    return out


@app.post("/api/relays", response_model=dict[str, Any])
def create_relay(
    body: RelayCreate,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _verify_admin(x_admin_token)
    r = Relay(
        name=body.name.strip(),
        base_url=body.base_url.strip().rstrip("/"),
        api_key=body.api_key.strip() if body.api_key and body.api_key.strip() else None,
        check_path=body.check_path.strip() or "/v1/models",
        enabled=body.enabled,
        rank_boost=body.rank_boost,
        group_name=body.group_name.strip() if body.group_name else None,
        site_price=body.site_price.strip() if body.site_price else None,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    d = r.to_public_dict()
    d["has_api_key"] = bool(r.api_key and r.api_key.strip())
    return d


@app.patch("/api/relays/{relay_id}", response_model=dict[str, Any])
def update_relay(
    relay_id: int,
    body: RelayUpdate,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _verify_admin(x_admin_token)
    r = db.query(Relay).filter(Relay.id == relay_id).one_or_none()
    if r is None:
        raise HTTPException(404, detail="relay 不存在")
    if body.name is not None:
        r.name = body.name.strip()
    if body.base_url is not None:
        r.base_url = body.base_url.strip().rstrip("/")
    if body.api_key is not None:
        r.api_key = body.api_key.strip() or None
    if body.check_path is not None:
        r.check_path = body.check_path.strip() or "/v1/models"
    if body.enabled is not None:
        r.enabled = body.enabled
    if body.rank_boost is not None:
        r.rank_boost = body.rank_boost
    if body.group_name is not None:
        r.group_name = body.group_name.strip() or None
    if body.site_price is not None:
        r.site_price = body.site_price.strip() or None
    if body.dilution_override is not None:
        r.dilution_override = body.dilution_override
    db.commit()
    db.refresh(r)
    d = r.to_public_dict()
    d["has_api_key"] = bool(r.api_key and r.api_key.strip())
    return d


@app.delete("/api/relays/{relay_id}", response_model=Message)
def delete_relay(
    relay_id: int,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    db: Session = Depends(get_db),
) -> Message:
    _verify_admin(x_admin_token)
    r = db.query(Relay).filter(Relay.id == relay_id).one_or_none()
    if r is None:
        raise HTTPException(404, detail="relay 不存在")
    db.delete(r)
    db.commit()
    return Message(message="deleted")


@app.post("/api/relays/{relay_id}/check")
def check_one(
    relay_id: int,
) -> JSONResponse:
    res, t = _probe_one_sync(relay_id)
    payload = result_to_dict(res)
    payload["checked_at"] = t
    payload["relay_id"] = relay_id
    return JSONResponse(content=payload)


@app.post("/api/probe-all")
def probe_all() -> JSONResponse:
    _probe_all_sync()
    return JSONResponse(content={"ok": True, "message": "all enabled relays probed"})


def main() -> None:
    import uvicorn

    uvicorn.run(
        "relay_probe.main:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


from relay_probe.pages import register_pages

register_pages(app)
