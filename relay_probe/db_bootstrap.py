"""首启时创建默认管理员、导入 JSON 种子（可选）。"""
import json
import logging
from pathlib import Path

from relay_probe.config import Settings
from relay_probe.database import SessionLocal
from relay_probe.models import Relay, User
from relay_probe.auth_security import hash_password

log = logging.getLogger("relay_probe.bootstrap")
settings = Settings()


def ensure_admin_user() -> None:
    if not (settings.init_admin_username and settings.init_admin_password):
        return
    db = SessionLocal()
    try:
        n = db.query(User).count()
        if n > 0:
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
            exists = (
                db.query(Relay)
                .filter(Relay.base_url == bu.rstrip("/"))
                .first()
            )
            if exists:
                continue
            r = Relay(
                name=name,
                base_url=bu.rstrip("/"),
                api_key=item.get("api_key") or None,
                check_path=item.get("check_path") or "/v1/models",
                enabled=bool(item.get("enabled", True)),
                group_name=(item.get("group") or None),
                site_price=(item.get("price") or None),
            )
            db.add(r)
            n += 1
        if n:
            db.commit()
            log.info("从 seed_sites.json 导入 %s 条中转", n)
        else:
            db.rollback()
    except Exception:  # noqa: BLE001
        db.rollback()
        log.exception("导入 seed 失败")
    finally:
        db.close()
    return n
