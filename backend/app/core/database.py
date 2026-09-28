from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

# Use DATABASE_URL if available, otherwise construct from SUPABASE settings
database_url = settings.DATABASE_URL
if not database_url:
    database_url = "sqlite:///./attendx_dev.db"

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url.startswith("sqlite"):
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
