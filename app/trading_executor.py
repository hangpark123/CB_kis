"""
매매 실행 모듈

TradingSignal을 기반으로 실제 주문을 실행하고,
포지션을 업데이트하며, 손절/익절 조건을 모니터링합니다.
"""

import datetime as dt
from sqlalchemy import select, and_
from .db import SessionLocal
from .models import TradingSignal, Trade, Position, TradingConfig
from .kis_api import order_buy, order_sell, get_current_price
from .trading_strategy import (
    get_trading_config,
    calculate_order_quantity,
    should_sell,
    get_today_trade_count
)


def execute_signals():
    """
    미실행 매매 신호를 조회하고 실제 주문 실행
    
    Returns:
        int: 실행된 주문 수
    """
    config = get_trading_config()
    
    if not config.is_enabled:
        print("⚠ 자동매매가 비활성화되어 있습니다.")
        return 0
    
    # 오늘 거래 횟수 체크
    today_count = get_today_trade_count()
    if today_count >= config.max_daily_trades:
        print(f"[!] 오늘 최대 거래 횟수 도달 ({today_count}/{config.max_daily_trades})")
        return 0
    
    with SessionLocal() as session:
        # 미실행 매수 신호 조회
        signals = session.execute(
            select(TradingSignal)
            .where(
                and_(
                    TradingSignal.is_executed == False,
                    TradingSignal.signal_type == "BUY",
                    TradingSignal.stock_code.isnot(None)
                )
            )
            .order_by(TradingSignal.signal_strength.desc())
            .limit(config.max_daily_trades - today_count)
        ).scalars().all()
        
        if not signals:
            print("ℹ 실행할 매매 신호가 없습니다.")
            return 0
        
        executed_count = 0
        
        for signal in signals:
            try:
                # 주문 수량 계산
                quantity, price, reason = calculate_order_quantity(
                    signal.stock_code,
                    signal.signal_strength,
                    config
                )
                
                if quantity == 0:
                    print(f"⚠ {signal.stock_code} 주문 스킵: {reason}")
                    continue
                
                # 시장가 매수 주문 실행
                order_no = order_buy(signal.stock_code, quantity, price=None)
                
                if not order_no:
                    # 주문 실패
                    trade = Trade(
                        signal_id=signal.signal_id,
                        stock_code=signal.stock_code,
                        corp_name_kr=signal.corp_name_kr,
                        trade_type="BUY",
                        order_type="MARKET",
                        price=price,
                        quantity=quantity,
                        total_amount=price * quantity,
                        order_no=None,
                        status="FAILED",
                        executed_at=None,
                        created_at=dt.datetime.now()
                    )
                    session.add(trade)
                    signal.is_executed = True
                    continue
                
                # 주문 성공 - Trade 기록
                trade = Trade(
                    signal_id=signal.signal_id,
                    stock_code=signal.stock_code,
                    corp_name_kr=signal.corp_name_kr,
                    trade_type="BUY",
                    order_type="MARKET",
                    price=price,
                    quantity=quantity,
                    total_amount=price * quantity,
                    order_no=order_no,
                    status="FILLED",  # 시장가 주문은 즉시 체결 가정
                    executed_at=dt.datetime.now(),
                    created_at=dt.datetime.now()
                )
                session.add(trade)
                
                # 신호 실행 완료 표시
                signal.is_executed = True
                
                # Position 업데이트 또는 생성
                position = session.execute(
                    select(Position).where(Position.stock_code == signal.stock_code)
                ).scalar_one_or_none()
                
                if position:
                    # 기존 포지션에 추가 매수
                    total_qty = position.quantity + quantity
                    total_cost = (position.avg_price * position.quantity) + (price * quantity)
                    position.avg_price = total_cost / total_qty
                    position.quantity = total_qty
                    position.current_price = price
                    position.unrealized_pnl = (price - position.avg_price) * total_qty
                    position.last_updated = dt.datetime.now()
                else:
                    # 새 포지션 생성
                    position = Position(
                        stock_code=signal.stock_code,
                        corp_name_kr=signal.corp_name_kr,
                        quantity=quantity,
                        avg_price=price,
                        current_price=price,
                        unrealized_pnl=0,
                        last_updated=dt.datetime.now()
                    )
                    session.add(position)
                
                executed_count += 1
                print(f"[OK] 매수 체결: {signal.stock_code} {signal.corp_name_kr} "
                      f"{quantity}주 @ {price:,}원")
            
            except Exception as e:
                print(f"✗ 주문 실행 오류 ({signal.stock_code}): {e}")
                continue
        
        session.commit()
        return executed_count


def update_positions():
    """
    보유 포지션의 현재가 및 평가손익 업데이트
    
    Returns:
        int: 업데이트된 포지션 수
    """
    with SessionLocal() as session:
        positions = session.execute(
            select(Position).where(Position.quantity > 0)
        ).scalars().all()
        
        if not positions:
            print("ℹ 보유 포지션이 없습니다.")
            return 0
        
        updated_count = 0
        
        for position in positions:
            try:
                price_info = get_current_price(position.stock_code)
                if not price_info:
                    continue
                
                current_price = price_info["current_price"]
                position.current_price = current_price
                position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
                position.last_updated = dt.datetime.now()
                
                updated_count += 1
                
                pnl_pct = ((current_price - position.avg_price) / position.avg_price) * 100
                print(f"  {position.stock_code} {position.corp_name_kr}: "
                      f"{position.quantity}주, 수익률 {pnl_pct:+.2f}%, "
                      f"평가손익 {position.unrealized_pnl:+,.0f}원")
            
            except Exception as e:
                print(f"✗ 포지션 업데이트 오류 ({position.stock_code}): {e}")
                continue
        
        session.commit()
        return updated_count


def monitor_positions():
    """
    보유 포지션 모니터링 및 손절/익절 실행
    
    Returns:
        int: 청산된 포지션 수
    """
    config = get_trading_config()
    
    if not config.is_enabled:
        print("⚠ 자동매매가 비활성화되어 있습니다.")
        return 0
    
    with SessionLocal() as session:
        positions = session.execute(
            select(Position).where(Position.quantity > 0)
        ).scalars().all()
        
        if not positions:
            return 0
        
        closed_count = 0
        
        for position in positions:
            try:
                # 청산 조건 체크
                should_close, reason = should_sell(position, config)
                
                if not should_close:
                    continue
                
                # 매도 주문 실행
                price_info = get_current_price(position.stock_code)
                if not price_info:
                    print(f"⚠ {position.stock_code} 시세 조회 실패 - 매도 스킵")
                    continue
                
                current_price = price_info["current_price"]
                order_no = order_sell(position.stock_code, position.quantity, price=None)
                
                if not order_no:
                    print(f"✗ {position.stock_code} 매도 주문 실패")
                    continue
                
                # Trade 기록
                trade = Trade(
                    signal_id=None,
                    stock_code=position.stock_code,
                    corp_name_kr=position.corp_name_kr,
                    trade_type="SELL",
                    order_type="MARKET",
                    price=current_price,
                    quantity=position.quantity,
                    total_amount=current_price * position.quantity,
                    order_no=order_no,
                    status="FILLED",
                    executed_at=dt.datetime.now(),
                    created_at=dt.datetime.now()
                )
                session.add(trade)
                
                # 포지션 청산
                realized_pnl = (current_price - position.avg_price) * position.quantity
                pnl_pct = ((current_price - position.avg_price) / position.avg_price) * 100
                
                position.quantity = 0
                position.unrealized_pnl = 0
                position.last_updated = dt.datetime.now()
                
                closed_count += 1
                print(f"[OK] 포지션 청산: {position.stock_code} {position.corp_name_kr} "
                      f"- {reason}, 실현손익 {realized_pnl:+,.0f}원 ({pnl_pct:+.2f}%)")
            
            except Exception as e:
                print(f"✗ 포지션 모니터링 오류 ({position.stock_code}): {e}")
                continue
        
        session.commit()
        return closed_count


# 테스트 코드
if __name__ == "__main__":
    print("=== 매매 실행 테스트 ===\n")
    
    # 1. 신호 실행
    print("1. 매매 신호 실행:")
    executed = execute_signals()
    print(f"   실행된 주문: {executed}개\n")
    
    # 2. 포지션 업데이트
    print("2. 포지션 업데이트:")
    updated = update_positions()
    print(f"   업데이트된 포지션: {updated}개\n")
    
    # 3. 포지션 모니터링
    print("3. 손절/익절 모니터링:")
    closed = monitor_positions()
    print(f"   청산된 포지션: {closed}개")
