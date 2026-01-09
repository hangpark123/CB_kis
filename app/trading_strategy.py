"""
매매 전략 엔진

NormEvent를 분석하여 매매 신호(TradingSignal)를 생성하고,
포지션 관리 로직을 제공합니다.
"""

import os
import datetime as dt
from sqlalchemy import select, and_, desc, func
from .db import SessionLocal
from .models import NormEvent, TradingSignal, Position, TradingConfig
from .kis_api import get_current_price, get_balance
from dotenv import load_dotenv

load_dotenv()


def get_trading_config():
    """
    현재 매매 설정 조회 (없으면 환경변수 기반으로 생성)
    
    Returns:
        TradingConfig: 매매 설정 객체
    """
    with SessionLocal() as session:
        config = session.execute(select(TradingConfig).limit(1)).scalar_one_or_none()
        
        if not config:
            # 환경변수에서 읽어서 초기 설정 생성
            config = TradingConfig(
                is_enabled=os.getenv("TRADING_ENABLED", "false").lower() == "true",
                use_mock_account=os.getenv("USE_MOCK_ACCOUNT", "true").lower() == "true",
                max_position_size=float(os.getenv("MAX_POSITION_SIZE", 1000000)),
                score_threshold=float(os.getenv("SCORE_THRESHOLD", 0.7)),
                stop_loss_pct=float(os.getenv("STOP_LOSS_PCT", 5.0)),
                take_profit_pct=float(os.getenv("TAKE_PROFIT_PCT", 10.0)),
                max_daily_trades=int(os.getenv("MAX_DAILY_TRADES", 10)),
                updated_at=dt.datetime.now()
            )
            session.add(config)
            session.commit()
            session.refresh(config)
        
        return config


def generate_signals(lookback_minutes=60):
    """
    최근 NormEvent를 분석하여 매매 신호 생성
    
    Args:
        lookback_minutes: 분석할 최근 시간 범위 (분)
    
    Returns:
        int: 생성된 신호 개수
    """
    config = get_trading_config()
    
    if not config.is_enabled:
        print("[!] 자동매매가 비활성화되어 있습니다. (TRADING_ENABLED=false)")
        return 0
    
    cutoff = dt.datetime.now() - dt.timedelta(minutes=lookback_minutes)
    
    with SessionLocal() as session:
        # 최근 이벤트 중 스코어가 높은 것 조회
        events = session.execute(
            select(NormEvent)
            .where(
                and_(
                    NormEvent.created_at >= cutoff,
                    NormEvent.score >= config.score_threshold,
                    NormEvent.stock_code.isnot(None)
                )
            )
            .order_by(desc(NormEvent.score))
        ).scalars().all()
        
        if not events:
            print(f"ℹ 최근 {lookback_minutes}분간 스코어 >= {config.score_threshold}인 이벤트 없음")
            return 0
        
        signal_count = 0
        
        for event in events:
            # 이미 신호가 생성된 이벤트는 스킵
            existing = session.execute(
                select(TradingSignal)
                .where(
                    and_(
                        TradingSignal.ref_norm_event_id == event.event_id,
                        TradingSignal.stock_code == event.stock_code
                    )
                )
            ).scalar_one_or_none()
            
            if existing:
                continue
            
            # 이미 보유 중인 종목은 스킵
            position = session.execute(
                select(Position).where(Position.stock_code == event.stock_code)
            ).scalar_one_or_none()
            
            if position and position.quantity > 0:
                print(f"ℹ {event.stock_code} 이미 보유 중 - 신호 생성 스킵")
                continue
            
            # 매수 신호 생성
            # 이벤트 타입에 따라 신호 강도 조정
            strength_bonus = 0.0
            if event.event_type in {"REFIX", "CONVERSION"}:
                strength_bonus = 0.1
            
            signal_strength = min(1.0, float(event.score or 0) + strength_bonus)
            
            signal = TradingSignal(
                stock_code=event.stock_code,
                corp_name_kr=event.corp_name_kr,
                signal_type="BUY",
                signal_strength=signal_strength,
                reason=event.headline or event.summary,
                ref_norm_event_id=event.event_id,
                is_executed=False,
                created_at=dt.datetime.now()
            )
            
            session.add(signal)
            signal_count += 1
            print(f"[OK] 매수 신호 생성: {event.stock_code} {event.corp_name_kr} "
                  f"(스코어: {event.score}, 강도: {signal_strength:.2f})")
        
        session.commit()
        return signal_count


def should_sell(position, config):
    """
    포지션 청산 조건 판단
    
    Args:
        position: Position 객체
        config: TradingConfig 객체
    
    Returns:
        tuple: (should_sell: bool, reason: str)
    """
    if not position or position.quantity <= 0:
        return False, ""
    
    # 현재가 조회
    price_info = get_current_price(position.stock_code)
    if not price_info:
        return False, "시세 조회 실패"
    
    current_price = price_info["current_price"]
    avg_price = float(position.avg_price)
    
    # 수익률 계산
    pnl_pct = ((current_price - avg_price) / avg_price) * 100
    
    # 손절 조건
    if pnl_pct <= -config.stop_loss_pct:
        return True, f"손절 ({pnl_pct:.2f}% < -{config.stop_loss_pct}%)"
    
    # 익절 조건
    if pnl_pct >= config.take_profit_pct:
        return True, f"익절 ({pnl_pct:.2f}% >= {config.take_profit_pct}%)"
    
    # TODO: 부정적 뉴스 발생 시 매도 로직 추가 가능
    
    return False, ""


def calculate_order_quantity(stock_code, signal_strength, config):
    """
    주문 수량 계산
    
    Args:
        stock_code: 종목코드
        signal_strength: 신호 강도 (0~1)
        config: TradingConfig 객체
    
    Returns:
        tuple: (quantity: int, price: int, reason: str)
    """
    # 현재가 조회
    price_info = get_current_price(stock_code)
    if not price_info:
        return 0, 0, "시세 조회 실패"
    
    current_price = price_info["current_price"]
    
    # 잔고 조회
    balance = get_balance()
    available_cash = balance["cash"]
    
    # 투자 금액 결정 (신호 강도에 비례)
    max_investment = min(config.max_position_size, available_cash * 0.3)  # 잔고의 30% 제한
    target_investment = max_investment * signal_strength
    
    # 수량 계산 (1주 단위)
    quantity = int(target_investment / current_price)
    
    if quantity <= 0:
        return 0, 0, "예수금 부족 또는 수량 0"
    
    total_cost = quantity * current_price
    
    if total_cost > available_cash:
        quantity = int(available_cash / current_price)
        if quantity <= 0:
            return 0, 0, "예수금 부족"
    
    return quantity, current_price, f"예수금: {available_cash:,}원, 투자: {quantity * current_price:,}원"


def get_today_trade_count():
    """
    오늘 실행된 거래 횟수 조회
    
    Returns:
        int: 거래 횟수
    """
    today_start = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    with SessionLocal() as session:
        count = session.execute(
            select(func.count(TradingSignal.signal_id))
            .where(
                and_(
                    TradingSignal.created_at >= today_start,
                    TradingSignal.is_executed == True
                )
            )
        ).scalar_one()
        
        return count


# 테스트 코드
if __name__ == "__main__":
    print("=== 매매 전략 테스트 ===\n")
    
    # 1. 설정 조회
    print("1. 매매 설정:")
    config = get_trading_config()
    print(f"   활성화: {config.is_enabled}")
    print(f"   스코어 임계값: {config.score_threshold}")
    print(f"   손절: {config.stop_loss_pct}%, 익절: {config.take_profit_pct}%")
    print(f"   최대 거래: {config.max_daily_trades}회/일\n")
    
    # 2. 신호 생성 테스트
    print("2. 매매 신호 생성 (최근 60분):")
    count = generate_signals(lookback_minutes=60)
    print(f"   생성된 신호: {count}개\n")
    
    # 3. 오늘 거래 횟수
    print("3. 오늘 거래 횟수:")
    today_count = get_today_trade_count()
    print(f"   {today_count}회")
