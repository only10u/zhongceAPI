"""Jinja2 页面、静态资源与认证 API 路由。"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, Request, Response
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
from relay_probe.dashboard_stats import build_full_dashboard
from relay_probe.model_catalog import TRACKED_MODELS
from relay_probe.ranking import build_ranking_rows

log = logging.getLogger("relay_probe.pages")
settings = Settings()

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


@router.get("/inclusion", response_class=HTMLResponse)
def page_inclusion(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("inclusion.html", _ctx(request))


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
    return JSONResponse(content=d)


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
