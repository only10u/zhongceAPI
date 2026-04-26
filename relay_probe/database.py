from collections.abc import Generator

from sqlalchemy import create_engine, event
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


def init_db() -> None:
    settings.data_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
