from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

if settings.PG_DSN:
    engine = create_engine(settings.PG_DSN, pool_pre_ping=True, future=True)
else:
    engine = create_engine("sqlite:///cb_scanner.db", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
