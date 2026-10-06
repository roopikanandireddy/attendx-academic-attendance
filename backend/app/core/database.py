from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import get_settings

settings = get_settings()

from pathlib import Path

# Use DATABASE_URL if available, otherwise construct from SUPABASE settings or use backend/attendx_dev.db
database_url = settings.DATABASE_URL
if not database_url:
    backend_dir = Path(__file__).resolve().parent.parent.parent
    db_file = backend_dir / "attendx_dev.db"
    database_url = f"sqlite:///{db_file.as_posix()}"


if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url.startswith("sqlite"):
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_timeout=15,
        pool_recycle=300,
        connect_args={"connect_timeout": 10},
    )

# Module 8 — Observability: Measure aggregate DB query execution duration
from app.core.observability import setup_db_timing_hooks
setup_db_timing_hooks(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
