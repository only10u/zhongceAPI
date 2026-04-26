from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_base_list(raw: str) -> set[str]:
    out: set[str] = set()
    for part in (raw or "").replace("\n", ",").split(","):
        p = part.strip()
        if p:
            out.add(p.rstrip("/").lower())
    return out


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
    # 排名统计窗口（API 可单独指定更大窗口，如日/周/月榜用至 720h）
    ranking_window_hours: int = Field(default=24, ge=1, le=744)
    # 逗号分隔的 base_url（会规范化：去尾 /、小写），在排名中固定先于其它条目；不改变真实探测结果
    ranking_pin_first_bases: str = Field(
        default="",
        description="e.g. https://dapicloud.com",
    )
    # 历史样本超过该天数会清理（启动与每轮探测后）
    sample_retention_days: int = Field(default=7, ge=1, le=90)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8765, ge=1, le=65535)
    # 对外可访问的站点根 URL（无尾斜杠），如 https://zhongapice.com；用于 /docs 服务地址、规范链接等
    public_base_url: str = Field(default="")
    # 反代后的 Host 白名单（逗号分隔），如 zhongapice.com,www.zhongapice.com；空表示不限制（开发或仅内网时）
    trusted_hosts: str = Field(default="")
    # 写接口（增删改中转）需携带 X-Admin-Token；空字符串表示不校验（仅适合内网/测试）
    admin_token: str = Field(default="")
    # JWT 鉴权（网页登录、用户工作台）；生产请设长随机串
    jwt_secret: str = Field(default="insecure-please-set-jwt-secret-in-env")
    jwt_expire_hours: int = Field(default=72, ge=1, le=720)
    # 首启时自动创建管理员（仅当尚无任何用户）
    init_admin_username: str = Field(default="")
    init_admin_password: str = Field(default="")
    # 是否开放自助注册
    allow_register: bool = Field(default=True)

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)

    @property
    def database_url(self) -> str:
        p = (self.data_path / "app.db").resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{p.as_posix()}"

    @property
    def pin_first_base_set(self) -> set[str]:
        return _parse_base_list(self.ranking_pin_first_bases)

    @property
    def public_origin(self) -> str:
        return (self.public_base_url or "").strip().rstrip("/")

    @property
    def cookie_secure(self) -> bool:
        """在 HTTPS 公网根地址时建议让 JWT Cookie 带 Secure。"""
        return self.public_origin.lower().startswith("https://")

    @property
    def trusted_host_list(self) -> list[str]:
        if not (self.trusted_hosts or "").strip():
            return []
        return [h.strip() for h in self.trusted_hosts.split(",") if h.strip()]


def check_url_for(base: str, check_path: str) -> str:
    base = base.rstrip("/")
    path = check_path if check_path.startswith("/") else f"/{check_path}"
    return f"{base}{path}"
