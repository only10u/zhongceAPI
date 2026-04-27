"""Jinja2 页面、静态资源与认证 API 路由。"""
from __future__ import annotations

import logging
from datetime import date as date_cls
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import json
import secrets
import string

from fastapi import APIRouter, Body, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
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
    ProbeReport,
    Relay,
    User,
)
from relay_probe.dashboard_stats import (
    build_full_dashboard,
    build_home_stats,
    build_relay_model_matrix,
)
from relay_probe.model_catalog import (
    TRACKED_MODELS,
    get_home_probe_model_by_slug,
    home_detector_models,
    inclusion_checkbox_slugs,
    match_models,
)
from relay_probe.probe import (
    chat_usage_to_dict,
    result_to_dict,
    run_chat_completions_usage,
    run_probe,
)
from relay_probe.probe_ui import build_report_ui
from relay_probe.ranking import build_ranking_rows
from relay_probe.relay_apply import apply_relay_update
from relay_probe.relay_rank_shelf import parse_rank_map_json
from relay_probe.schemas import (
    HeartbeatIn,
    InclusionStatusUpdate,
    RelayCreate,
    RelayUpdate,
)
from starlette.concurrency import run_in_threadpool

log = logging.getLogger("relay_probe.pages")
settings = Settings()

# 公网试探测频控：按 IP 滑动窗口
_probe_hits: dict[str, list[float]] = {}
_report_hits: dict[str, list[float]] = {}


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


def _check_report_rl(ip: str, max_per_hour: int = 40) -> None:
    import time

    now = time.time()
    win = 3600.0
    lst = _report_hits.setdefault(ip, [])
    lst[:] = [t for t in lst if now - t < win]
    if len(lst) >= max_per_hour:
        raise HTTPException(429, detail="分享报告过于频繁，请稍后再试")
    lst.append(now)


def _new_report_public_id() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(12))


BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
COOKIE = "zhongce_token"
router = APIRouter(tags=["ui"])

# 排行页日/周/月三套窗口与表格（每套含多模型分表 + 总榜）
RANK_LEADERBOARDS: list[dict[str, Any]] = [
    {"key": "day", "label_zh": "日榜", "label_en": "24h", "hours": 24},
    {"key": "week", "label_zh": "周榜", "label_en": "7d", "hours": 168},
    {"key": "month", "label_zh": "月榜", "label_en": "30d", "hours": 720},
]


def _inclusion_model_groups() -> list[tuple[str, list[dict[str, Any]]]]:
    by_slug = {m["slug"]: m for m in home_detector_models()}
    specs = [
        ("Claude", ["opus-47", "opus-46", "sonnet-46"]),
        ("OpenAI", ["gpt-55", "gpt-54"]),
        ("Google", ["gemini-31-pro"]),
    ]
    out: list[tuple[str, list[dict[str, Any]]]] = []
    for label, slugs in specs:
        out.append((label, [by_slug[s] for s in slugs if s in by_slug]))
    return out


def _build_rank_periods(db: Session) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in RANK_LEADERBOARDS:
        h = int(p["hours"])
        d = build_full_dashboard(db, window_hours=h)
        out.append(
            {
                **p,
                "legacy_rows": build_ranking_rows(db, window_hours=h),
                "dashboard": d,
            }
        )
    return out


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
    o = (settings.public_origin or "").strip()
    av = (settings.static_asset_version or "").strip()
    static_q = f"?v={av}" if av else ""
    return {
        "request": request,
        "user": u,
        "version": __version__,
        "site_url": o,
        "static_q": static_q,
        **extra,
    }


@router.get("/", response_class=HTMLResponse)
def page_home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "home.html", _ctx(request, models_ui=home_detector_models())
    )


@router.get("/rank", response_class=HTMLResponse)
def page_rank(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    rank_periods = _build_rank_periods(db)
    return templates.TemplateResponse(
        "rank.html",
        _ctx(
            request,
            rank_periods=rank_periods,
            tracked=TRACKED_MODELS,
            inclusion_groups=_inclusion_model_groups(),
        ),
    )


@router.get("/yiyuan", response_class=HTMLResponse)
def page_yiyuan(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """一元模型：实付单价公式说明 + 计算器 + 已收录站点参考表。"""
    rels = (
        db.query(Relay)
        .filter(Relay.enabled.is_(True))
        .order_by(Relay.id)
        .all()
    )
    yiyuan_rows = [
        {
            "id": r.id,
            "name": r.name,
            "base_url": r.base_url,
            "group": r.group_name or "—",
            "price": r.site_price or "—",
        }
        for r in rels
    ]
    return templates.TemplateResponse(
        "yiyuan.html", _ctx(request, yiyuan_relays=yiyuan_rows)
    )


@router.get("/inclusion", response_class=HTMLResponse)
def page_inclusion(request: Request) -> RedirectResponse:
    return RedirectResponse("/rank#inclusion", status_code=302)


@router.get("/inclusion/status", response_class=HTMLResponse)
def page_inclusion_status(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("inclusion_status.html", _ctx(request))


@router.get("/report/{public_id}", response_class=HTMLResponse)
def page_probe_report(
    request: Request,
    public_id: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    raw = (public_id or "").strip()
    if not raw or len(raw) > 20 or not raw.isalnum():
        raise HTTPException(404, detail="未找到该报告")
    pr = (
        db.query(ProbeReport)
        .filter(ProbeReport.public_id == raw)
        .one_or_none()
    )
    if pr is None:
        raise HTTPException(404, detail="未找到该报告")
    try:
        report_payload: dict[str, Any] = json.loads(pr.payload_json)
    except json.JSONDecodeError:
        raise HTTPException(500, detail="报告数据损坏")
    return templates.TemplateResponse(
        "report.html",
        _ctx(
            request,
            report_payload=report_payload,
            public_id=raw,
            report_saved_at=pr.created_at,
        ),
    )


@router.post("/api/probe-reports")
def api_create_probe_report(
    request: Request,
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    _check_report_rl(_client_ip(request))
    if not isinstance(body, dict) or int(body.get("version") or 0) != 1:
        raise HTTPException(400, detail="version 需为 1")
    data = body.get("data")
    if not isinstance(data, dict):
        raise HTTPException(400, detail="需要 data 对象")
    line = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if len(line) > 64 * 1024:
        raise HTTPException(400, detail="数据过大，请缩短后重试")
    max_attempts = 10
    for _ in range(max_attempts):
        pid = _new_report_public_id()
        pr = ProbeReport(public_id=pid, payload_json=line)
        db.add(pr)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        root = (settings.public_origin or "").strip().rstrip("/")
        if not root:
            root = str(request.base_url).rstrip("/")
        return JSONResponse(
            {
                "ok": True,
                "public_id": pid,
                "url": f"{root}/report/{pid}",
            }
        )
    raise HTTPException(500, detail="请稍后重试")


@router.get("/api/presence")
def api_presence() -> JSONResponse:
    from relay_probe import presence

    return JSONResponse(
        {
            "online": presence.count_online(),
            "ttl_sec": int(presence.TTL_SEC),
        }
    )


@router.post("/api/presence/heartbeat")
def api_presence_heartbeat(body: HeartbeatIn) -> JSONResponse:
    from relay_probe import presence

    n = presence.touch(body.visitor_id)
    return JSONResponse(
        {
            "ok": True,
            "online": n,
            "ttl_sec": int(presence.TTL_SEC),
        }
    )


@router.get("/api/admin/traffic")
def api_admin_traffic(
    request: Request,
    days: int = 30,
    db: Session = Depends(get_db),
) -> JSONResponse:
    u = _user_from_cookie(request)
    if not u or not u.get("is_admin"):
        raise HTTPException(403, detail="需要管理员")
    if days < 1 or days > 366:
        raise HTTPException(400, detail="days 应在 1–366 之间")
    from relay_probe.traffic_store import list_daily_series

    return JSONResponse({"series": list_daily_series(db, days)})


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
    relay_edit_list = [
        {"relay": r, "rank_map": parse_rank_map_json(r.rank_models_json)}
        for r in rels
    ]
    return templates.TemplateResponse(
        "admin.html",
        _ctx(
            request,
            relay_rows=rels,
            relay_edit_list=relay_edit_list,
            user_rows=urows,
            inc_rows=inc,
            tracked_models_list=TRACKED_MODELS,
            tracked_slugs=[m["slug"] for m in TRACKED_MODELS],
        ),
    )


# --- API JSON for SPA parts ---
@router.get("/api/rank-bundles")
def api_rank_bundles(db: Session = Depends(get_db)) -> JSONResponse:
    """日/周/月三套排行 JSON，供排行页单请求轮询。"""
    now = datetime.now(timezone.utc).isoformat()
    out: dict[str, Any] = {
        "version": __version__,
        "updated_at": now,
    }
    for p in RANK_LEADERBOARDS:
        h = int(p["hours"])
        key = str(p["key"])
        d = build_full_dashboard(db, window_hours=h)
        out[key] = {
            "window_hours": h,
            "models_meta": d["models_meta"],
            "by_model": d["by_model"],
            "legacy": build_ranking_rows(db, window_hours=h),
        }
    return JSONResponse(content=out)


@router.get("/api/dashboard")
def api_dashboard(
    window_hours: int | None = None,
    db: Session = Depends(get_db),
) -> JSONResponse:
    h = window_hours or settings.ranking_window_hours
    if h < 1 or h > 744:
        raise HTTPException(400, detail="window_hours 应在 1–744 之间")
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
    if h < 1 or h > 744:
        raise HTTPException(400, detail="window_hours 应在 1–744 之间")
    out = build_home_stats(db, window_hours=h)
    out["version"] = __version__
    return JSONResponse(content=out)


@router.get("/api/relay-matrix")
def api_relay_matrix(
    window_hours: int | None = None,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """全站 站点×模型 矩阵 JSON（各目标线；数据来本库探测）。"""
    h = window_hours or settings.ranking_window_hours
    if h < 1 or h > 744:
        raise HTTPException(400, detail="window_hours 应在 1–744 之间")
    out = build_relay_model_matrix(db, window_hours=h)
    out["version"] = __version__
    return JSONResponse(content=out)


def _kuma_service_status(
    res: object,
    model_matches: dict[str, bool],
    selected_slug: str = "opus-47",
    *,
    model_defs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """对齐 Uptime Kuma 式状态：up / degraded / down + 各目标线摘要；标记当前选中模型。"""
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
    defs = model_defs if model_defs is not None else TRACKED_MODELS
    total = len(defs)
    hit = sum(1 for m in defs if model_matches.get(m["slug"]))
    model_detail: list[dict[str, Any]] = []
    for m in defs:
        slug = m["slug"]
        model_detail.append(
            {
                "slug": slug,
                "name_zh": m["name_zh"],
                "name_en": m["name_en"],
                "card_id": m.get("card_id", ""),
                "present": bool(model_matches.get(slug)),
                "selected": slug == selected_slug,
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
        "selected_slug": selected_slug,
    }


@router.post("/api/try-probe")
async def api_try_probe(
    request: Request,
    base_url: str = Form(...),
    api_key: str = Form(""),
    model_slug: str = Form("opus-47"),
) -> JSONResponse:
    """
    在线检测：固定 GET `/v1/models`（与排行同源），
    由 `model_slug` 指定「主评」目标线；在返回体中子串匹配全部已收录目标线。
    """
    _check_probe_rl(_client_ip(request))
    bu = (base_url or "").strip()
    if not bu.startswith(("http://", "https://")):
        raise HTTPException(
            400, detail="请填写以 http:// 或 https:// 开头的 API 根地址"
        )
    if len(bu) > 2048:
        raise HTTPException(400, detail="地址过长")
    msel = (model_slug or "opus-47").strip()
    tr = get_home_probe_model_by_slug(msel)
    if tr is None:
        raise HTTPException(400, detail="请从在线检测模型卡片中选择其一")
    path = "/v1/models"
    key = api_key.strip() or None
    if key and len(key) > 4096:
        raise HTTPException(400, detail="Key 过长")
    res = await run_in_threadpool(
        run_probe, bu, path, float(settings.http_timeout_sec), key
    )
    chat_usage: dict[str, Any]
    if key:
        cu = await run_in_threadpool(
            run_chat_completions_usage,
            bu,
            str(tr.get("card_id", "")),
            float(settings.http_timeout_sec),
            key,
        )
        chat_usage = chat_usage_to_dict(cu)
    else:
        chat_usage = {
            "skipped": True,
            "reason": "no_api_key",
            "ok": False,
            "usage_parsed": False,
        }
    matches: dict[str, bool] = {}
    if res.body_text:
        matches = match_models(res.body_text.lower(), scope="home_try")
    out = result_to_dict(res, include_body=False)
    out["model_matches"] = matches
    out["check_path_used"] = path
    out["primary_model"] = {
        "slug": msel,
        "name_zh": tr["name_zh"],
        "card_id": tr.get("card_id", ""),
        "present": bool(matches.get(msel)),
    }
    kuma = _kuma_service_status(
        res, matches, msel, model_defs=home_detector_models()
    )
    out["service_status"] = kuma
    out["checked_at"] = datetime.now(timezone.utc).isoformat()
    out["probe_base_url"] = bu
    out["chat_usage"] = chat_usage
    out["report_ui"] = build_report_ui(res, matches, msel, tr, chat_usage=chat_usage)
    return JSONResponse(content=out)


@router.post("/api/inclusion")
def api_inclusion(
    site_name: str = Form(...),
    site_url: str = Form(...),
    founded_date: str = Form(...),
    signup_url: str = Form(...),
    contact_person: str = Form(...),
    contact: str = Form(...),
    suggested_group: str = Form(""),
    remark: str = Form(""),
    probe_account: str = Form(...),
    probe_password: str = Form(...),
    supported_models: list[str] | None = Form(None),
    db: Session = Depends(get_db),
) -> JSONResponse:
    allowed = inclusion_checkbox_slugs()
    raw_models = list(supported_models) if supported_models is not None else []
    models_clean = [x for x in raw_models if x in allowed]
    pw = (probe_password or "").strip()
    if len(pw) < 9:
        raise HTTPException(400, detail="探测用密码须长于 8 位，且建议包含大小写、数字与特殊字符")
    try:
        fd = date_cls.fromisoformat((founded_date or "").strip()[:10])
    except ValueError as e:
        raise HTTPException(400, detail="成立时间无效，请使用 YYYY-MM-DD") from e
    ir = InclusionRequest(
        site_name=site_name.strip()[:256],
        site_url=site_url.strip()[:1024],
        founded_date=fd,
        signup_url=(signup_url or "").strip()[:1024] or None,
        contact_person=contact_person.strip()[:256] or None,
        contact=contact.strip()[:512] or None,
        suggested_group=(suggested_group or "").strip()[:128] or None,
        remark=(remark or "")[:4000] or None,
        probe_account=(probe_account or "").strip()[:512] or None,
        probe_password=(probe_password or "")[:512] or None,
        supported_models_json=json.dumps(models_clean, ensure_ascii=False),
        status="pending",
    )
    db.add(ir)
    db.commit()
    db.refresh(ir)
    return JSONResponse({"ok": True, "id": ir.id})


@router.get("/api/inclusion/lookup")
def api_inclusion_lookup(id: int, db: Session = Depends(get_db)) -> JSONResponse:
    row = (
        db.query(InclusionRequest).filter(InclusionRequest.id == id).one_or_none()
    )
    if row is None:
        raise HTTPException(404, detail="未找到该申请编号")
    return JSONResponse(
        {
            "id": row.id,
            "site_name": row.site_name,
            "status": row.status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
    )


@router.patch("/api/admin/inclusion-requests/{req_id}")
def admin_patch_inclusion(
    request: Request,
    req_id: int,
    body: InclusionStatusUpdate,
    db: Session = Depends(get_db),
) -> JSONResponse:
    u = _user_from_cookie(request)
    if not u or not u.get("is_admin"):
        raise HTTPException(403, detail="需要管理员")
    row = (
        db.query(InclusionRequest).filter(InclusionRequest.id == req_id).one_or_none()
    )
    if row is None:
        raise HTTPException(404, detail="申请不存在")
    row.status = body.status
    db.commit()
    return JSONResponse({"ok": True, "id": row.id, "status": row.status})


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
        secure=settings.cookie_secure,
    )
    return res


@router.post("/api/auth/logout")
def api_logout() -> JSONResponse:
    r = JSONResponse({"ok": True})
    r.delete_cookie(COOKIE, path="/", secure=settings.cookie_secure)
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
        secure=settings.cookie_secure,
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


@router.post("/api/admin/relays")
def admin_create_relay(
    request: Request,
    body: RelayCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    u = _user_from_cookie(request)
    if not u or not u.get("is_admin"):
        raise HTTPException(403, detail="需要管理员")
    r = Relay(
        name=body.name.strip(),
        base_url=body.base_url.strip().rstrip("/"),
        api_key=body.api_key.strip() if body.api_key and body.api_key.strip() else None,
        check_path=body.check_path.strip() or "/v1/models",
        enabled=body.enabled,
        rank_boost=body.rank_boost,
        group_name=body.group_name.strip() if body.group_name else None,
        site_price=body.site_price.strip() if body.site_price else None,
        pricing_input_usd=body.pricing_input_usd.strip()
        if body.pricing_input_usd
        else None,
        pricing_output_usd=body.pricing_output_usd.strip()
        if body.pricing_output_usd
        else None,
        price_sort_key=body.price_sort_key,
        dilution_label=body.dilution_label.strip() if body.dilution_label else None,
        dilution_override=body.dilution_override,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    d = r.to_public_dict()
    d["has_api_key"] = bool(r.api_key and r.api_key.strip())
    return d


@router.patch("/api/admin/relays/{relay_id}")
def admin_update_relay(
    request: Request,
    relay_id: int,
    body: RelayUpdate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    u = _user_from_cookie(request)
    if not u or not u.get("is_admin"):
        raise HTTPException(403, detail="需要管理员")
    r = db.query(Relay).filter(Relay.id == relay_id).one_or_none()
    if r is None:
        raise HTTPException(404, detail="relay 不存在")
    apply_relay_update(r, body)
    db.commit()
    db.refresh(r)
    d = r.to_public_dict()
    d["has_api_key"] = bool(r.api_key and r.api_key.strip())
    return d


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
