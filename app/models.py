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

class TradingSignal(Base):
    """매매 신호 테이블"""
    __tablename__ = "trading_signals"
    signal_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str | None] = mapped_column(VARCHAR(12))
    corp_name_kr: Mapped[str | None] = mapped_column(Text)
    signal_type: Mapped[str] = mapped_column(Text)  # 'BUY' | 'SELL'
    signal_strength: Mapped[float] = mapped_column(Numeric)  # 0~1
    reason: Mapped[str | None] = mapped_column(Text)  # 신호 이유 (뉴스 헤드라인)
    ref_norm_event_id: Mapped[int | None] = mapped_column(Integer)
    is_executed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))

class Trade(Base):
    """실제 매매 기록 테이블"""
    __tablename__ = "trades"
    trade_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[int | None] = mapped_column(Integer)
    stock_code: Mapped[str] = mapped_column(VARCHAR(12))
    corp_name_kr: Mapped[str | None] = mapped_column(Text)
    trade_type: Mapped[str] = mapped_column(Text)  # 'BUY' | 'SELL'
    order_type: Mapped[str] = mapped_column(Text)  # 'MARKET' | 'LIMIT'
    price: Mapped[float] = mapped_column(Numeric)
    quantity: Mapped[int] = mapped_column(Integer)
    total_amount: Mapped[float] = mapped_column(Numeric)
    order_no: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)  # 'PENDING' | 'FILLED' | 'CANCELLED' | 'FAILED'
    executed_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))

class Position(Base):
    """보유 포지션 테이블"""
    __tablename__ = "positions"
    position_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(VARCHAR(12), unique=True)
    corp_name_kr: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column(Integer)
    avg_price: Mapped[float] = mapped_column(Numeric)
    current_price: Mapped[float] = mapped_column(Numeric)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric)
    last_updated: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))

class TradingConfig(Base):
    """매매 설정 테이블"""
    __tablename__ = "trading_config"
    config_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    use_mock_account: Mapped[bool] = mapped_column(Boolean, default=True)
    max_position_size: Mapped[float] = mapped_column(Numeric)  # 종목당 최대 투자금액
    score_threshold: Mapped[float] = mapped_column(Numeric)  # 매수 신호 임계값
    stop_loss_pct: Mapped[float] = mapped_column(Numeric)
    take_profit_pct: Mapped[float] = mapped_column(Numeric)
    max_daily_trades: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))

