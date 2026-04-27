"""掺水率格与在线率展示：表格仅显示百分比数字；无人工时按目录探测推算。"""

from __future__ import annotations

from relay_probe.models import Relay


def clamp_pct_1_100(n: float) -> int:
    return max(1, min(100, int(round(n))))


def format_online_rate_pct(rate_0_1: float | None, *, samples: int) -> str:
    """目录/通路成功率：两位小数，避免整数一律 100% 的观感。"""
    if not samples or rate_0_1 is None:
        return "—"
    p = float(rate_0_1) * 100.0
    return f"{p:.2f}%"


def dilution_cell_percent(
    r: Relay,
    *,
    samples: int,
    rate_0_1: float,
) -> str:
    """
    掺水率格：仅「整数%」形式，范围 1–100。
    - 后台填写 dilution_override：直接显示该整数（掺水程度，越高越差）。
    - 未填：按目录命中推算掺水风险：100 − 命中百分点，夹在 1–100。
    - 无样本：—
    """
    if r.dilution_override is not None:
        return f"{clamp_pct_1_100(float(r.dilution_override))}%"
    if samples <= 0:
        return "—"
    hit = clamp_pct_1_100(float(rate_0_1) * 100.0)
    risk = max(1, min(100, 100 - hit))
    return f"{risk}%"


def dilution_pct_numeric(
    r: Relay,
    *,
    samples: int,
    rate_0_1: float,
) -> int | None:
    """与 dilution_cell_percent 一致的可排序整数 1–100；无样本为 None。"""
    if r.dilution_override is not None:
        return clamp_pct_1_100(float(r.dilution_override))
    if samples <= 0:
        return None
    hit = clamp_pct_1_100(float(rate_0_1) * 100.0)
    return max(1, min(100, 100 - hit))
