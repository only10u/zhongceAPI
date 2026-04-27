from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from relay_probe.config import Settings
from relay_probe.models import Base

settings = Settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _sqlite_enforce_fk(
    dbapi_connection: object,
    _connection_record: object,
) -> None:
    u = str(settings.database_url)
    if not u.startswith("sqlite"):
        return
    c = dbapi_connection.cursor()  # type: ignore[union-attr]
    c.execute("PRAGMA foreign_keys=ON")
    c.close()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _ensure_relay_columns() -> None:
    if not str(settings.database_url).startswith("sqlite"):
        return
    alters = [
        ("rank_boost", "ALTER TABLE relays ADD COLUMN rank_boost INTEGER NOT NULL DEFAULT 0"),
        ("group_name", "ALTER TABLE relays ADD COLUMN group_name VARCHAR(64)"),
        ("site_price", "ALTER TABLE relays ADD COLUMN site_price VARCHAR(64)"),
        ("dilution_override", "ALTER TABLE relays ADD COLUMN dilution_override FLOAT"),
        ("dilution_label", "ALTER TABLE relays ADD COLUMN dilution_label VARCHAR(64)"),
        (
            "pricing_input_usd",
            "ALTER TABLE relays ADD COLUMN pricing_input_usd VARCHAR(64)",
        ),
        (
            "pricing_output_usd",
            "ALTER TABLE relays ADD COLUMN pricing_output_usd VARCHAR(64)",
        ),
        ("price_sort_key", "ALTER TABLE relays ADD COLUMN price_sort_key FLOAT"),
    ]
    with engine.begin() as conn:
        r = conn.execute(text("PRAGMA table_info(relays)"))
        names = {row[1] for row in r.all()}
        for col, ddl in alters:
            if col not in names:
                conn.execute(text(ddl))
                names.add(col)


def _ensure_inclusion_and_rank_json_columns() -> None:
    if not str(settings.database_url).startswith("sqlite"):
        return
    relay_alters = [
        (
            "rank_models_json",
            "ALTER TABLE relays ADD COLUMN rank_models_json TEXT",
        ),
    ]
    inc_alters = [
        (
            "relay_id",
            # 旧库 ALTER 不加 REFERENCES，避免部分 SQLite 版本失败；逻辑层仍校验中继 ID
            "ALTER TABLE inclusion_requests ADD COLUMN relay_id INTEGER UNIQUE",
        ),
        ("founded_date", "ALTER TABLE inclusion_requests ADD COLUMN founded_date DATE"),
        ("signup_url", "ALTER TABLE inclusion_requests ADD COLUMN signup_url VARCHAR(1024)"),
        ("contact_person", "ALTER TABLE inclusion_requests ADD COLUMN contact_person VARCHAR(256)"),
        ("suggested_group", "ALTER TABLE inclusion_requests ADD COLUMN suggested_group VARCHAR(128)"),
        ("supported_models_json", "ALTER TABLE inclusion_requests ADD COLUMN supported_models_json TEXT"),
        ("probe_account", "ALTER TABLE inclusion_requests ADD COLUMN probe_account VARCHAR(512)"),
        ("probe_password", "ALTER TABLE inclusion_requests ADD COLUMN probe_password VARCHAR(512)"),
    ]
    with engine.begin() as conn:
        r = conn.execute(text("PRAGMA table_info(relays)"))
        rnames = {row[1] for row in r.all()}
        for col, ddl in relay_alters:
            if col not in rnames:
                conn.execute(text(ddl))
                rnames.add(col)
        r2 = conn.execute(text("PRAGMA table_info(inclusion_requests)"))
        inames = {row[1] for row in r2.all()}
        for col, ddl in inc_alters:
            if col not in inames:
                conn.execute(text(ddl))
                inames.add(col)


def init_db() -> None:
    settings.data_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _ensure_relay_columns()
    _ensure_inclusion_and_rank_json_columns()
    from relay_probe.db_bootstrap import ensure_admin_user, import_seed_sites_from_json

    ensure_admin_user()
    import_seed_sites_from_json()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
