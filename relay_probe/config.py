from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 多中转：数据目录（相对项目根）
    data_dir: str = Field(default="data")
    http_timeout_sec: float = Field(default=15.0, ge=1.0, le=120.0)
    # 0 = 不后台轮询；>0 为每轮「全部启用中转」探完后的休眠秒数
    check_interval_sec: int = Field(default=0, ge=0)
    # 排名统计窗口
    ranking_window_hours: int = Field(default=24, ge=1, le=168)
    # 历史样本超过该天数会清理（启动与每轮探测后）
    sample_retention_days: int = Field(default=7, ge=1, le=90)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8765, ge=1, le=65535)
    # 写接口（增删改中转）需携带 X-Admin-Token；空字符串表示不校验（仅适合内网/测试）
    admin_token: str = Field(default="")

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)

    @property
    def database_url(self) -> str:
        p = (self.data_path / "app.db").resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{p.as_posix()}"


def check_url_for(base: str, check_path: str) -> str:
    base = base.rstrip("/")
    path = check_path if check_path.startswith("/") else f"/{check_path}"
    return f"{base}{path}"
