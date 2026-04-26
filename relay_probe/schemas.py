from pydantic import BaseModel, Field


class RelayCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    base_url: str = Field(min_length=1, max_length=1024, description="无尾斜杠")
    api_key: str | None = Field(default=None, max_length=2048)
    check_path: str = Field(default="/v1/models", max_length=512)
    enabled: bool = True


class RelayUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    base_url: str | None = Field(default=None, min_length=1, max_length=1024)
    api_key: str | None = Field(default=None, max_length=2048)
    check_path: str | None = Field(default=None, min_length=1, max_length=512)
    enabled: bool | None = None


class Message(BaseModel):
    message: str
