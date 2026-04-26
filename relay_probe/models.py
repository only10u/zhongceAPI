from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
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
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    samples: Mapped[list["ProbeSample"]] = relationship(
        "ProbeSample", back_populates="relay", lazy="selectin"
    )

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "check_path": self.check_path,
            "enabled": self.enabled,
            "rank_boost": self.rank_boost,
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
