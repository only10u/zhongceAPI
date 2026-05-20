from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from relay_probe.config import Settings

settings = Settings()
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALG = "HS256"


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_access_token(
    sub: str, user_id: int, is_admin: bool, expires_hours: int | None = None
) -> str:
    h = expires_hours if expires_hours is not None else settings.jwt_expire_hours
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=h)
    payload: dict[str, Any] = {
        "sub": sub,
        "uid": user_id,
        "adm": is_admin,
        "exp": exp,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALG)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALG])
    except JWTError:
        return None


def create_password_reset_token(
    user_id: int,
    username: str,
    email: str,
    expires_minutes: int | None = None,
) -> str:
    m = expires_minutes if expires_minutes is not None else settings.password_reset_expire_minutes
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=m)
    payload: dict[str, Any] = {
        "uid": user_id,
        "sub": username,
        "email": email,
        "exp": exp,
        "typ": "pwd_reset",
    }
    return jwt.encode(payload, settings.password_reset_secret, algorithm=ALG)


def decode_password_reset_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token, settings.password_reset_secret, algorithms=[ALG]
        )
    except JWTError:
        return None
    if payload.get("typ") != "pwd_reset":
        return None
    return payload
