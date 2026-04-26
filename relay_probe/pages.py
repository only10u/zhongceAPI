"""Jinja2 页面、静态资源与认证 API 路由。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from relay_probe import __version__
from relay_probe.auth_security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from relay_probe.config import Settings
from relay_probe.database import get_db
from relay_probe.db_bootstrap import import_seed_sites_from_json
from relay_probe.models import (
    InclusionRequest,
    Relay,
    User,
)
from relay_probe.dashboard_stats import (
    build_full_dashboard,
    build_home_stats,
    build_relay_model_matrix,
)
from relay_probe.model_catalog import TRACKED_MODELS, match_models
from relay_probe.probe import result_to_dict, run_probe
from relay_probe.ranking import build_ranking_rows
from starlette.concurrency import run_in_threadpool

log = logging.getLogger("relay_probe.pages")
settings = Settings()

# 公网试探测频控：按 IP 滑动窗口
_probe_hits: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    xff = (request.headers.get("x-forwarded-for") or "").split(",")
    if xff and xff[0].strip():
        return xff[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _check_probe_rl(ip: str, max_per_hour: int = 40) -> None:
    import time

    now = time.time()
    win = 3600.0
    lst = _probe_hits.setdefault(ip, [])
    lst[:] = [t for t in lst if now - t < win]
    if len(lst) >= max_per_hour:
        raise HTTPException(429, detail="试探测过于频繁，请 1 小时后再试或直接使用排行数据")
    lst.append(now)


BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
COOKIE = "zhongce_token"
router = APIRouter(tags=["ui"])


def _user_from_cookie(request: Request) -> dict | None:
    raw = request.cookies.get(COOKIE)
    if not raw:
        return None
    p = decode_token(raw)
    if not p:
        return None
    return {
        "username": p.get("sub", ""),
        "id": p.get("uid", 0),
        "is_admin": bool(p.get("adm", False)),
    }


def _ctx(request: Request, **extra) -> dict:
    u = _user_from_cookie(request)
    return {
        "request": request,
        "user": u,
        "version": __version__,
        **extra,
    }


@router.get("/", response_class=HTMLResponse)
def page_home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("home.html", _ctx(request))


@router.get("/rank", response_class=HTMLResponse)
def page_rank(
    request: Request,
    window_hours: int | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    h = window_hours or settings.ranking_window_hours
    legacy = build_ranking_rows(db, window_hours=h)
    dash = build_full_dashboard(db, window_hours=h)
    return templates.TemplateResponse(
        "rank.html",
        _ctx(
            request,
            window_hours=h,
            legacy_rows=legacy,
            dashboard=dash,
            tracked=TRACKED_MODELS,
        ),
    )


@router.get("/inclusion")
def page_inclusion_redirect() -> RedirectResponse:
    return RedirectResponse(url="/rank#inclusion", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def page_login(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", _ctx(request))


@router.get("/workspace", response_class=HTMLResponse)
def page_workspace(request: Request) -> HTMLResponse:
    u = _user_from_cookie(request)
    if not u:
        return RedirectResponse("/login?next=/workspace", status_code=302)
    return templates.TemplateResponse("workspace.html", _ctx(request, wuser=u))


@router.get("/admin", response_class=HTMLResponse)
def page_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    u = _user_from_cookie(request)
    if not u or not u.get("is_admin"):
        return RedirectResponse("/login?next=/admin", status_code=302)
    rels = db.query(Relay).order_by(Relay.id).all()
    urows = db.query(User).order_by(User.id).all()
    inc = (
        db.query(InclusionRequest)
        .order_by(InclusionRequest.created_at.desc())
        .limit(100)
        .all()
    )
    return templates.TemplateResponse(
        "admin.html",
        _ctx(
            request,
            relay_rows=rels,
            user_rows=urows,
            inc_rows=inc,
        ),
    )


# --- API JSON for SPA parts ---
@router.get("/api/dashboard")
def api_dashboard(
    window_hours: int | None = None,
    db: Session = Depends(get_db),
) -> JSONResponse:
    h = window_hours or settings.ranking_window_hours
    d = build_full_dashboard(db, window_hours=h)
    d["version"] = __version__
    d["updated_at"] = datetime.now(timezone.utc).isoformat()
    d["legacy"] = build_ranking_rows(db, window_hours=h)
    return JSONResponse(content=d)


@router.get("/api/home-stats")
def api_home_stats(
    window_hours: int | None = None,
    db: Session = Depends(get_db),
) -> JSONResponse:
    h = window_hours or settings.ranking_window_hours
    out = build_home_stats(db, window_hours=h)
    out["version"] = __version__
    return JSONResponse(content=out)


@router.get("/api/relay-matrix")
def api_relay_matrix(
    window_hours: int | None = None,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """全站 站点乘模型 矩阵 JSON（与 hvoy.ai 同六线目标；数据来本库探测）。"""
    h = window_hours or settings.ranking_window_hours
    out = build_relay_model_matrix(db, window_hours=h)
    out["version"] = __version__
    return JSONResponse(content=out)


def _kuma_service_status(
    res: object, model_matches: dict[str, bool]
) -> dict[str, Any]:
    """对齐 Uptime Kuma 式状态：up / degraded / down + 六线摘要。"""
    st = "down"
    sc = getattr(res, "http_status", None)
    if getattr(res, "error", None) and sc is None:
        st = "down"
    elif sc is not None and 200 <= int(sc) < 300:
        st = "up"
    elif sc is not None and int(sc) in (401, 403, 422, 429):
        st = "degraded"
    elif sc is not None and 300 <= int(sc) < 500:
        st = "degraded"
    else:
        st = "down"
    total = len(TRACKED_MODELS)
    hit = sum(1 for m in TRACKED_MODELS if model_matches.get(m["slug"]))
    model_detail: list[dict[str, Any]] = []
    for m in TRACKED_MODELS:  # 与 hvoy 首页六线目标一致
        slug = m["slug"]
        model_detail.append(
            {
                "slug": slug,
                "name_zh": m["name_zh"],
                "name_en": m["name_en"],
                "present": bool(model_matches.get(slug)),
            }
        )
    return {
        "status": st,
        "status_emoji": {"up": "🟢", "degraded": "🟡", "down": "🔴"}.get(
            st, "⚪"
        ),
        "http_status": sc,
        "model_hits": hit,
        "model_tracked": total,
        "model_hit_ratio": round(hit / total, 3) if total else 0.0,
        "model_detail": model_detail,
    }


@router.post("/api/try-probe")
async def api_try_probe(
    request: Request,
    base_url: str = Form(...),
    api_key: str = Form(""),
    check_path: str = Form("/v1/models"),
) -> JSONResponse:
    _check_probe_rl(_client_ip(request))
    bu = (base_url or "").strip()
    if not bu.startswith(("http://", "https://")):
        raise HTTPException(
            400, detail="请填写以 http:// 或 https:// 开头的 API 根地址"
        )
    if len(bu) > 2048:
        raise HTTPException(400, detail="地址过长")
    path = (check_path or "/v1/models").strip() or "/v1/models"
    if len(path) > 512 or not path.startswith("/"):
        raise HTTPException(400, detail="检测路径需为以 / 开头的相对路径")
    key = api_key.strip() or None
    if key and len(key) > 4096:
        raise HTTPException(400, detail="Key 过长")
    res = await run_in_threadpool(
        run_probe, bu, path, float(settings.http_timeout_sec), key
    )
    matches: dict[str, bool] = {}
    if res.body_text:
        matches = match_models(res.body_text.lower())
    out = result_to_dict(res, include_body=False)
    out["model_matches"] = matches
    out["check_path_used"] = path
    kuma = _kuma_service_status(res, matches)
    out["service_status"] = kuma
    out["checked_at"] = datetime.now(timezone.utc).isoformat()
    return JSONResponse(content=out)


@router.post("/api/inclusion")
def api_inclusion(
    site_name: str = Form(...),
    site_url: str = Form(...),
    contact: str = Form(""),
    remark: str = Form(""),
    db: Session = Depends(get_db),
) -> JSONResponse:
    ir = InclusionRequest(
        site_name=site_name.strip()[:256],
        site_url=site_url.strip()[:1024],
        contact=contact.strip()[:512] or None,
        remark=remark[:4000] or None,
    )
    db.add(ir)
    db.commit()
    return JSONResponse({"ok": True, "id": ir.id})


@router.post("/api/auth/login")
def api_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    u = (
        db.query(User)
        .filter(User.username == username.strip())
        .one_or_none()
    )
    if u is None or not verify_password(password, u.password_hash):
        raise HTTPException(401, detail="用户名或密码错误")
    token = create_access_token(u.username, u.id, u.is_admin)
    res = JSONResponse({"ok": True, "token": token, "is_admin": u.is_admin})
    max_age = settings.jwt_expire_hours * 3600
    res.set_cookie(
        COOKIE,
        token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return res


@router.post("/api/auth/logout")
def api_logout() -> JSONResponse:
    r = JSONResponse({"ok": True})
    r.delete_cookie(COOKIE, path="/")
    return r


@router.post("/api/auth/register")
def api_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    if not settings.allow_register:
        raise HTTPException(403, detail="已关闭注册")
    if len(username) < 2 or len(username) > 32:
        raise HTTPException(400, detail="用户名长度 2-32")
    if len(password) < 6:
        raise HTTPException(400, detail="密码至少 6 位")
    exists = (
        db.query(User).filter(User.username == username.strip()).first()
    )
    if exists:
        raise HTTPException(400, detail="用户名已存在")
    u = User(
        username=username.strip(),
        password_hash=hash_password(password),
        is_admin=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    token = create_access_token(u.username, u.id, u.is_admin)
    r = JSONResponse({"ok": True, "token": token, "is_admin": False})
    r.set_cookie(
        COOKIE,
        token,
        max_age=settings.jwt_expire_hours * 3600,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return r


@router.get("/api/auth/me")
def api_me(request: Request) -> JSONResponse:
    u = _user_from_cookie(request)
    if not u:
        return JSONResponse({"user": None})
    return JSONResponse({"user": u})


@router.post("/api/auth/change-password")
def api_change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    cur = _user_from_cookie(request)
    if not cur:
        raise HTTPException(401, detail="未登录")
    if len(new_password) < 8:
        raise HTTPException(400, detail="新密码至少 8 位")
    u = db.query(User).filter(User.id == int(cur["id"])).one_or_none()
    if u is None or not verify_password(old_password, u.password_hash):
        raise HTTPException(400, detail="原密码错误")
    u.password_hash = hash_password(new_password)
    db.commit()
    return JSONResponse({"ok": True})


@router.post("/api/admin/reseed")
def admin_reseed(
    request: Request,
    x_admin_token: str | None = None,
) -> JSONResponse:
    if settings.admin_token and (
        (request.headers.get("X-Admin-Token") or "").strip()
        != settings.admin_token.strip()
    ):
        raise HTTPException(401, detail="admin")
    n = import_seed_sites_from_json()
    return JSONResponse({"ok": True, "imported": n})


def register_pages(app: FastAPI) -> None:
    static_dir = BASE / "static"
    if static_dir.is_dir():
        app.mount(
            "/static", StaticFiles(directory=str(static_dir)), name="static"
        )
    app.include_router(router)
