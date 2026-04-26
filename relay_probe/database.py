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
    with engine.begin() as conn:
        r = conn.execute(text("PRAGMA table_info(relays)"))
        names = {row[1] for row in r.all()}
        if "rank_boost" not in names:
            conn.execute(
                text("ALTER TABLE relays ADD COLUMN rank_boost INTEGER NOT NULL DEFAULT 0")
            )


def init_db() -> None:
    settings.data_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _ensure_relay_columns()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
