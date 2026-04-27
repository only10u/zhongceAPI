from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Relay(Base):
    __tablename__ = "relays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    base_url: Mapped[str] = mapped_column(String(1024))
    api_key: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    check_path: Mapped[str] = mapped_column(String(512), default="/v1/models")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # 仅影响排序权值（越大越靠前），与 RANKING_PIN_FIRST_BASES 可叠加
    rank_boost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 展示用（可选）
    group_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    site_price: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # 展示用定价文案（首页/排行表头：输入/$、输出/$）
    pricing_input_usd: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pricing_output_usd: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # 用于「按价格」排序：数值越小通常表示越便宜（如 实付元/百万Token），未填则排后
    price_sort_key: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # 人工备注掺水率 0-100 或空（深度探测可后续接）
    dilution_override: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # 掺水率展示文案（如「几乎不」），优先生于纯数字
    dilution_label: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # JSON：各模型线在分榜/矩阵中是否上架，如 {"gpt-55":false}；缺省或未写 slug 视为上架
    rank_models_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    samples: Mapped[list["ProbeSample"]] = relationship(
        "ProbeSample", back_populates="relay", lazy="selectin"
    )
    model_samples: Mapped[list["ModelProbeSample"]] = relationship(
        "ModelProbeSample", back_populates="relay"
    )

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "check_path": self.check_path,
            "enabled": self.enabled,
            "rank_boost": self.rank_boost,
            "group_name": self.group_name,
            "site_price": self.site_price,
            "pricing_input_usd": self.pricing_input_usd,
            "pricing_output_usd": self.pricing_output_usd,
            "price_sort_key": self.price_sort_key,
            "dilution_label": self.dilution_label,
            "dilution_override": self.dilution_override,
            "rank_models_json": self.rank_models_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ProbeSample(Base):
    __tablename__ = "probe_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    relay_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("relays.id", ondelete="CASCADE"), index=True
    )
    ok: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False, index=True
    )

    relay: Mapped[Relay] = relationship("Relay", back_populates="samples")


class ModelProbeSample(Base):
    """一次探测里，在 /v1/models 正文中子串是否命中各模型线号（低成本可用性，非对话质检）。"""

    __tablename__ = "model_probe_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    relay_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("relays.id", ondelete="CASCADE"), index=True
    )
    model_slug: Mapped[str] = mapped_column(String(64), index=True)
    present: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False, index=True
    )
    relay: Mapped[Relay] = relationship("Relay", back_populates="model_samples")


class TrafficDay(Base):
    """站可见页面 GET 的日 PV 聚合（UTC 日期）。"""

    __tablename__ = "traffic_days"

    day: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    page_views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ProbeReport(Base):
    """首页「分享报告」可读的 JSON 快照（短 id 公链，不含用户 Key）。"""

    __tablename__ = "probe_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False, index=True
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )


class InclusionRequest(Base):
    __tablename__ = "inclusion_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_name: Mapped[str] = mapped_column(String(256))
    site_url: Mapped[str] = mapped_column(String(1024))
    # 成立日期（按日）
    founded_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    signup_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    contact: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    suggested_group: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # JSON 数组：申报支持的模型线 slug
    supported_models_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 申报用于自动探测的测试账号（管理员在后台可再调整；数据库仅存摘要）
    probe_account: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    probe_password: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="pending"
    )  # pending, approved, rejected
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False, index=True
    )
