from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    relay_base_url: str = Field(
        default="",
        description="Base URL of the relay, no trailing slash",
    )
    relay_api_key: str = Field(default="")
    relay_check_path: str = Field(default="/v1/models")
    http_timeout_sec: float = Field(default=15.0, ge=1.0, le=120.0)
    check_interval_sec: int = Field(
        default=0,
        ge=0,
        description="0 = no background loop; else period in seconds",
    )
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8765, ge=1, le=65535)

    @property
    def check_url(self) -> str:
        base = self.relay_base_url.rstrip("/")
        path = self.relay_check_path if self.relay_check_path.startswith("/") else f"/{self.relay_check_path}"
        return f"{base}{path}"
