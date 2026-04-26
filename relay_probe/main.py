import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from relay_probe import __version__
from relay_probe.config import Settings
from relay_probe.database import SessionLocal, get_db, init_db
from relay_probe.models import ProbeSample, Relay
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

_PAGE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>中转站检测排名</title>
  <style>
    :root { --bg: #0f1419; --fg: #e7e9ea; --muted: #8b98a5; --border: #38444d; --accent: #1d9bf0; }
    * { box-sizing: border-box; }
    body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      background: var(--bg); color: var(--fg); margin: 0; padding: 1.25rem; line-height: 1.45; }
    h1 { font-size: 1.25rem; font-weight: 600; margin: 0 0 0.5rem; }
    p.meta { color: var(--muted); font-size: 0.85rem; margin: 0 0 1rem; }
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th, td { text-align: left; padding: 0.5rem 0.6rem; border-bottom: 1px solid var(--border); }
    th { color: var(--muted); font-weight: 500; }
    tr:hover td { background: rgba(29, 155, 240, 0.06); }
    .ok { color: #00ba7c; }
    .bad { color: #f4212e; }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <h1>中转站检测排名</h1>
  <p class="meta" id="meta">加载中…</p>
  <div style="overflow-x: auto">
    <table>
      <thead>
        <tr>
          <th>排名</th>
          <th>名称</th>
          <th>窗口成功率</th>
          <th>平均延迟 (ms)</th>
          <th>最近</th>
          <th>Base</th>
        </tr>
      </thead>
      <tbody id="rows"></tbody>
    </table>
  </div>
  <p class="meta"><a href="/api/ranking">JSON</a> · <a href="/docs">API 文档</a></p>
  <script>
    async function load() {
      const r = await fetch("/api/ranking?window_hours=" + encodeURIComponent("__WINDOW_HOURS__"), { cache: "no-store" });
      const d = await r.json();
      document.getElementById("meta").textContent = "统计窗口: " + d.window_hours + " 小时 · 共 " + d.rows.length + " 条";
      const tb = document.getElementById("rows");
      tb.innerHTML = "";
      for (const x of d.rows) {
        const tr = document.createElement("tr");
        const last = x.last_check_at
          ? (x.last_ok ? "<span class=ok>成功</span>" : "<span class=bad>失败</span>") + " " + (x.last_latency_ms != null ? x.last_latency_ms + " ms" : "")
          : "—";
        tr.innerHTML = "<td>" + x.rank + "</td><td>" + escapeHtml(x.name) + "</td><td>" +
          (x.samples_in_window ? (x.success_rate * 100).toFixed(1) + "%" : "—") + "</td><td>" +
          (x.avg_latency_ms != null ? x.avg_latency_ms : "—") + "</td><td>" + last + "</td><td><small>" + escapeHtml(x.base_url) + "</small></td>";
        tb.appendChild(tr);
      }
    }
    function escapeHtml(s) {
      return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
    }
    load();
    setInterval(load, 30000);
  </script>
</body>
</html>"""


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
                    False, None, None, "relay 不存在", None
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
            ProbeResult(False, None, None, "数据库写入失败", None),
            None,
        )
    finally:
        db.close()


app = FastAPI(
    title="多中转站探测与排名",
    version=__version__,
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> HTMLResponse:
    wh = str(settings.ranking_window_hours)
    return HTMLResponse(content=_PAGE_HTML.replace("__WINDOW_HOURS__", wh))


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
