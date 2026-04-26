"""首启时创建默认管理员、导入 JSON 种子（可选）。"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from relay_probe.config import Settings
from relay_probe.database import SessionLocal
from relay_probe.models import Relay, User
from relay_probe.auth_security import hash_password

log = logging.getLogger("relay_probe.bootstrap")
settings = Settings()


def ensure_admin_user() -> None:
    if not (settings.init_admin_username and settings.init_admin_password):
        log.info("首启管理员：未设置 INIT_ADMIN_USERNAME / INIT_ADMIN_PASSWORD，跳过")
        return
    db = SessionLocal()
    try:
        n = db.query(User).count()
        if n > 0:
            log.info("首启管理员：users 表已有 %s 条记录，跳过（仅空库时创建）", n)
            return
        u = User(
            username=settings.init_admin_username.strip(),
            password_hash=hash_password(settings.init_admin_password),
            is_admin=True,
        )
        db.add(u)
        db.commit()
        log.info("已创建初始管理员: %s", u.username)
    except Exception:  # noqa: BLE001
        db.rollback()
        log.exception("创建初始管理员失败")
    finally:
        db.close()


def import_seed_sites_from_json() -> int:
    p = settings.data_path / "seed_sites.json"
    if not p.is_file():
        return 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        log.warning("无法读取 seed_sites.json")
        return 0
    if not isinstance(data, list):
        return 0
    db = SessionLocal()
    n = 0
    try:
        for item in data:
            if not isinstance(item, dict):
                continue
            if item.get("_readme") or item.get("_comment"):
                continue
            name = (item.get("name") or "").strip()
            bu = (item.get("base_url") or "").strip()
            if not name or not bu:
                continue
            bu_n = bu.rstrip("/")
            dlab = item.get("dilution_label")
            dovr = item.get("dilution_override")
            dflt: Optional[float] = None
            if dovr is not None and str(dovr).strip() != "":
                try:
                    dflt = float(dovr)
                except (TypeError, ValueError):
                    dflt = None
            check_path = (item.get("check_path") or "/v1/models").strip() or "/v1/models"
            enabled = bool(item.get("enabled", True))
            gname = (item.get("group") or None)
            sprice = (item.get("price") or None)
            dilab = (str(dlab).strip() if dlab else None)
            key_raw = item.get("api_key")
            key: str | None
            if key_raw is None:
                key = None
            else:
                key = str(key_raw).strip() or None

            exists = (
                db.query(Relay)
                .filter(Relay.base_url == bu_n)
                .first()
            )
            if exists:
                # 同 base 再次出现在 seed 中时：更新名称、Key、价格等（便于同步多机）
                exists.name = name
                if "api_key" in item:
                    exists.api_key = key
                exists.check_path = check_path
                exists.enabled = enabled
                if gname is not None:
                    exists.group_name = gname
                if sprice is not None:
                    exists.site_price = sprice
                if dilab is not None:
                    exists.dilution_label = dilab
                if dflt is not None:
                    exists.dilution_override = dflt
                n += 1
                continue
            r = Relay(
                name=name,
                base_url=bu_n,
                api_key=key,
                check_path=check_path,
                enabled=enabled,
                group_name=gname,
                site_price=sprice,
                dilution_label=dilab,
                dilution_override=dflt,
            )
            db.add(r)
            n += 1
        if n:
            db.commit()
            log.info("从 seed_sites.json 新增或更新 %s 条中转", n)
        else:
            db.rollback()
    except Exception:  # noqa: BLE001
        db.rollback()
        log.exception("导入 seed 失败")
    finally:
        db.close()
    return n
