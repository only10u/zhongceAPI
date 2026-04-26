from pydantic import BaseModel, Field


class RelayCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    base_url: str = Field(min_length=1, max_length=1024, description="无尾斜杠")
    api_key: str | None = Field(default=None, max_length=2048)
    check_path: str = Field(default="/v1/models", max_length=512)
    enabled: bool = True
    rank_boost: int = Field(default=0, ge=0, le=2_000_000_000)
    group_name: str | None = Field(default=None, max_length=64)
    site_price: str | None = Field(default=None, max_length=64)
    dilution_label: str | None = Field(default=None, max_length=64)
    dilution_override: float | None = Field(default=None, ge=0, le=100)


class RelayUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    base_url: str | None = Field(default=None, min_length=1, max_length=1024)
    api_key: str | None = Field(default=None, max_length=2048)
    check_path: str | None = Field(default=None, min_length=1, max_length=512)
    enabled: bool | None = None
    rank_boost: int | None = Field(default=None, ge=0, le=2_000_000_000)
    group_name: str | None = None
    site_price: str | None = None
    dilution_label: str | None = Field(default=None, max_length=64)
    dilution_override: float | None = Field(default=None, ge=0, le=100)


class Message(BaseModel):
    message: str


class HeartbeatIn(BaseModel):
    visitor_id: str = Field(min_length=8, max_length=96)
