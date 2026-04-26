"""内存中的在线心跳：多 worker 不共享，单机估算。"""

from __future__ import annotations

import threading
import time

_LOCK = threading.Lock()
_PRESENCE: dict[str, float] = {}
TTL_SEC = 120.0


def touch(visitor_id: str) -> int:
    """记录访客 id 并返回当前在线人数（约 TTL_SEC 内有心跳的独立 id 数）。"""
    vid = (visitor_id or "").strip()[:96]
    if len(vid) < 8:
        return count_online()
    now = time.time()
    with _LOCK:
        _PRESENCE[vid] = now
        _prune_locked(now)
        return len(_PRESENCE)


def count_online() -> int:
    now = time.time()
    with _LOCK:
        _prune_locked(now)
        return len(_PRESENCE)


def _prune_locked(now: float) -> None:
    dead = [k for k, t in _PRESENCE.items() if now - t > TTL_SEC]
    for k in dead:
        del _PRESENCE[k]
