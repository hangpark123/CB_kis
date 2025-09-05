# app/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, Text, Boolean, TIMESTAMP, Numeric, VARCHAR, JSON

class Base(DeclarativeBase):
    pass

class DimListing(Base):
    __tablename__ = "dim_listing"
    stock_code: Mapped[str] = mapped_column(VARCHAR(12), primary_key=True)
    corp_name_kr: Mapped[str] = mapped_column(Text)
    market: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

class RawEvent(Base):
    __tablename__ = "raw_events"
    # ✅ SQLite 호환: INTEGER PRIMARY KEY AUTOINCREMENT
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(Text)               # 'dart' | 'naver_news'
    url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    corp_name_kr: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))
    raw_json: Mapped[dict | None] = mapped_column(JSON)
    inserted_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))

class NormEvent(Base):
    __tablename__ = "norm_events"
    # ✅ SQLite 호환
    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str | None] = mapped_column(VARCHAR(12))
    corp_name_kr: Mapped[str | None] = mapped_column(Text)
    event_type: Mapped[str] = mapped_column(Text)           # 'ISSUE'|'REFIX'|'CONVERSION'|'REDEMPTION'|'OTHER'
    headline: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Numeric)
    has_official: Mapped[bool] = mapped_column(Boolean, default=False)
    ref_raw_ids: Mapped[str | None] = mapped_column(Text)   # CSV 문자열 보관
    event_time: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))
