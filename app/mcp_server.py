"""
MCP (Model Context Protocol) 서버

Claude Desktop에서 대화로 주식 조회, 매매 신호 확인, 주문 실행 등을 
할 수 있게 해주는 MCP 서버입니다.
"""

import asyncio
import sys
import os
from datetime import datetime

# MCP SDK
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# 프로젝트 모듈
from .kis_api import get_current_price, get_balance, order_buy, order_sell
from .trading_strategy import generate_signals, get_trading_config
from .trading_executor import execute_signals, update_positions, monitor_positions
from .models import TradingSignal, Trade, Position, NormEvent
from .db import SessionLocal
from sqlalchemy import select, desc, and_

# MCP 서버 생성
server = Server("cb-trading-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """사용 가능한 도구 목록 반환"""
    return [
        Tool(
            name="get_stock_price",
            description="주식의 현재가를 조회합니다. 종목코드(6자리)를 입력하세요.",
            inputSchema={
                "type": "object",
                "properties": {
                    "stock_code": {
                        "type": "string",
                        "description": "종목코드 (6자리, 예: 005930은 삼성전자)"
                    }
                },
                "required": ["stock_code"]
            }
        ),
        Tool(
            name="get_balance",
            description="계좌 잔고 및 보유 종목을 조회합니다. 예수금, 총 평가금액, 보유 종목 목록을 확인할 수 있습니다.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_positions",
            description="현재 보유 중인 포지션(종목)을 조회합니다. 평균단가, 현재가, 수익률 등을 확인할 수 있습니다.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_trading_signals",
            description="뉴스 기반으로 생성된 매매 신호를 조회합니다. 최근 CB 관련 이벤트를 기반으로 매수/매도 신호를 확인할 수 있습니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "조회할 신호 개수 (기본: 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_recent_trades",
            description="최근 매매 내역을 조회합니다. 체결된 주문 내역을 확인할 수 있습니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "조회할 거래 개수 (기본: 20)",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="search_cb_news",
            description="전환사채(CB) 관련 최근 뉴스/공시를 검색합니다. 리픽싱, 전환청구, 조기상환 등의 이벤트를 확인할 수 있습니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "검색 키워드 (회사명, 종목코드 등, 선택사항)"
                    },
                    "limit": {
                        "type": "number",
                        "description": "조회할 뉴스 개수 (기본: 15)",
                        "default": 15
                    }
                }
            }
        ),
        Tool(
            name="order_buy_stock",
            description="주식을 매수합니다. 시장가 주문으로 즉시 체결됩니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "stock_code": {
                        "type": "string",
                        "description": "종목코드 (6자리)"
                    },
                    "quantity": {
                        "type": "number",
                        "description": "매수 수량 (주)"
                    }
                },
                "required": ["stock_code", "quantity"]
            }
        ),
        Tool(
            name="order_sell_stock",
            description="주식을 매도합니다. 시장가 주문으로 즉시 체결됩니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "stock_code": {
                        "type": "string",
                        "description": "종목코드 (6자리)"
                    },
                    "quantity": {
                        "type": "number",
                        "description": "매도 수량 (주)"
                    }
                },
                "required": ["stock_code", "quantity"]
            }
        ),
        Tool(
            name="generate_trading_signals",
            description="최근 뉴스를 분석하여 매매 신호를 생성합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "lookback_minutes": {
                        "type": "number",
                        "description": "분석할 과거 시간 범위 (분, 기본: 120)",
                        "default": 120
                    }
                }
            }
        ),
        Tool(
            name="execute_pending_orders",
            description="대기 중인 매매 신호를 실제 주문으로 실행합니다.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_trading_config",
            description="현재 자동매매 설정을 조회합니다. 활성화 여부, 손절/익절 기준 등을 확인할 수 있습니다.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="toggle_auto_trading",
            description="자동매매를 켜거나 끕니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "enable": {
                        "type": "boolean",
                        "description": "true=자동매매 시작, false=자동매매 중지"
                    }
                },
                "required": ["enable"]
            }
        ),
        Tool(
            name="get_performance",
            description="투자 성과를 조회합니다. 실현손익, 미실현손익, 승률 등을 확인할 수 있습니다.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """도구 실행"""
    
    try:
        if name == "get_stock_price":
            stock_code = arguments["stock_code"]
            price_info = get_current_price(stock_code)
            
            if not price_info:
                return [TextContent(
                    type="text",
                    text=f"❌ {stock_code} 시세 조회 실패. 종목코드를 확인해주세요."
                )]
            
            result = f"""📈 **{price_info['stock_name']} ({stock_code})**

💰 현재가: {price_info['current_price']:,}원
📊 등락률: {price_info['change_rate']:+.2f}%
📈 고가: {price_info['high']:,}원
📉 저가: {price_info['low']:,}원
🔓 시가: {price_info['open']:,}원
📦 거래량: {price_info['volume']:,}주
"""
            return [TextContent(type="text", text=result)]
        
        elif name == "get_balance":
            balance = get_balance()
            
            result = f"""💰 **계좌 정보**

💵 예수금: {balance['cash']:,}원
📊 총 평가: {balance['total_value']:,}원
📈 평가손익: {balance.get('pnl', 0):+,}원

"""
            if balance['positions']:
                result += "**📌 보유 종목**\n\n"
                for i, pos in enumerate(balance['positions'], 1):
                    pnl_emoji = "🔴" if pos['pnl_rate'] < 0 else "🟢"
                    result += f"{i}. **{pos['stock_name']}** ({pos['stock_code']})\n"
                    result += f"   {pos['quantity']:,}주 | 평단: {pos['avg_price']:,}원 | 수익률: {pnl_emoji} {pos['pnl_rate']:+.2f}%\n\n"
            else:
                result += "보유 종목이 없습니다.\n"
            
            return [TextContent(type="text", text=result)]
        
        elif name == "get_positions":
            with SessionLocal() as session:
                positions = session.execute(
                    select(Position).where(Position.quantity > 0)
                ).scalars().all()
                
                if not positions:
                    return [TextContent(type="text", text="현재 보유 중인 포지션이 없습니다.")]
                
                result = "📌 **보유 포지션**\n\n"
                total_unrealized = 0
                for i, pos in enumerate(positions, 1):
                    pnl_rate = ((pos.current_price - pos.avg_price) / pos.avg_price * 100)
                    pnl_emoji = "🔴" if pnl_rate < 0 else "🟢"
                    
                    result += f"{i}. **{pos.corp_name_kr or ''}** ({pos.stock_code})\n"
                    result += f"   수량: {pos.quantity:,}주\n"
                    result += f"   평단: {pos.avg_price:,.0f}원 | 현재가: {pos.current_price:,.0f}원\n"
                    result += f"   평가손익: {pnl_emoji} {pos.unrealized_pnl:+,.0f}원 ({pnl_rate:+.2f}%)\n\n"
                    total_unrealized += float(pos.unrealized_pnl)
                
                result += f"**총 미실현손익: {'+' if total_unrealized >= 0 else ''}{total_unrealized:,.0f}원**"
                
                return [TextContent(type="text", text=result)]
        
        elif name == "get_trading_signals":
            limit = int(arguments.get("limit", 10))
            
            with SessionLocal() as session:
                signals = session.execute(
                    select(TradingSignal)
                    .order_by(desc(TradingSignal.created_at))
                    .limit(limit)
                ).scalars().all()
                
                if not signals:
                    return [TextContent(type="text", text="생성된 매매 신호가 없습니다.")]
                
                result = f"💡 **최근 매매 신호 ({len(signals)}개)**\n\n"
                for i, sig in enumerate(signals, 1):
                    sig_emoji = "🟢" if sig.signal_type == "BUY" else "🔴"
                    status_emoji = "✅" if sig.is_executed else "⏳"
                    
                    result += f"{i}. {sig_emoji} **{sig.signal_type}** - {sig.corp_name_kr or ''} ({sig.stock_code})\n"
                    result += f"   강도: {float(sig.signal_strength or 0)*100:.0f}% | 상태: {status_emoji}\n"
                    result += f"   이유: {sig.reason or '-'}\n"
                    result += f"   생성: {sig.created_at}\n\n"
                
                return [TextContent(type="text", text=result)]
        
        elif name == "get_recent_trades":
            limit = int(arguments.get("limit", 20))
            
            with SessionLocal() as session:
                trades = session.execute(
                    select(Trade)
                    .order_by(desc(Trade.created_at))
                    .limit(limit)
                ).scalars().all()
                
                if not trades:
                    return [TextContent(type="text", text="매매 내역이 없습니다.")]
                
                result = f"📋 **최근 매매 내역 ({len(trades)}건)**\n\n"
                for i, t in enumerate(trades, 1):
                    trade_emoji = "🟢" if t.trade_type == "BUY" else "🔴"
                    status = "✅ 체결" if t.status == "FILLED" else "❌ 실패" if t.status == "FAILED" else "⏳ 대기"
                    
                    result += f"{i}. {trade_emoji} **{t.trade_type}** - {t.corp_name_kr or ''} ({t.stock_code})\n"
                    result += f"   {t.quantity:,}주 × {t.price:,.0f}원 = {t.total_amount:,.0f}원\n"
                    result += f"   {status} | {t.created_at}\n\n"
                
                return [TextContent(type="text", text=result)]
        
        elif name == "search_cb_news":
            keyword = arguments.get("keyword", "")
            limit = int(arguments.get("limit", 15))
            
            with SessionLocal() as session:
                query = select(NormEvent).order_by(desc(NormEvent.created_at))
                
                if keyword:
                    query = query.where(
                        (NormEvent.corp_name_kr.contains(keyword)) |
                        (NormEvent.stock_code.contains(keyword)) |
                        (NormEvent.headline.contains(keyword))
                    )
                
                events = session.execute(query.limit(limit)).scalars().all()
                
                if not events:
                    return [TextContent(type="text", text=f"'{keyword}' 관련 뉴스를 찾을 수 없습니다.")]
                
                result = f"📰 **CB 관련 뉴스** ({len(events)}건)\n\n"
                for i, evt in enumerate(events, 1):
                    event_type_emoji = {
                        "REFIX": "🔄",
                        "CONVERSION": "💱",
                        "REDEMPTION": "💰",
                        "ISSUE": "📢",
                        "OTHER": "📄"
                    }.get(evt.event_type, "📄")
                    
                    result += f"{i}. {event_type_emoji} **{evt.event_type}** - {evt.corp_name_kr or ''} ({evt.stock_code or ''})\n"
                    result += f"   {evt.headline or evt.summary or ''}\n"
                    result += f"   스코어: {float(evt.score or 0):.2f} | {evt.created_at}\n\n"
                
                return [TextContent(type="text", text=result)]
        
        elif name == "order_buy_stock":
            stock_code = arguments["stock_code"]
            quantity = int(arguments["quantity"])
            
            # 현재가 조회
            price_info = get_current_price(stock_code)
            if not price_info:
                return [TextContent(type="text", text=f"❌ {stock_code} 종목을 찾을 수 없습니다.")]
            
            # 매수 주문
            order_no = order_buy(stock_code, quantity, price=None)
            
            if order_no:
                result = f"""✅ **매수 주문 성공**

📈 {price_info['stock_name']} ({stock_code})
📊 수량: {quantity:,}주
💰 예상 금액: 약 {price_info['current_price'] * quantity:,}원
🔢 주문번호: {order_no}

주문이 체결되었습니다!
"""
            else:
                result = "❌ 매수 주문이 실패했습니다. 계좌번호 및 잔고를 확인해주세요."
            
            return [TextContent(type="text", text=result)]
        
        elif name == "order_sell_stock":
            stock_code = arguments["stock_code"]
            quantity = int(arguments["quantity"])
            
            # 현재가 조회
            price_info = get_current_price(stock_code)
            if not price_info:
                return [TextContent(type="text", text=f"❌ {stock_code} 종목을 찾을 수 없습니다.")]
            
            # 매도 주문
            order_no = order_sell(stock_code, quantity, price=None)
            
            if order_no:
                result = f"""✅ **매도 주문 성공**

📉 {price_info['stock_name']} ({stock_code})
📊 수량: {quantity:,}주
💰 예상 금액: 약 {price_info['current_price'] * quantity:,}원
🔢 주문번호: {order_no}

주문이 체결되었습니다!
"""
            else:
                result = "❌ 매도 주문이 실패했습니다. 보유 수량을 확인해주세요."
            
            return [TextContent(type="text", text=result)]
        
        elif name == "generate_trading_signals":
            lookback = int(arguments.get("lookback_minutes", 120))
            count = generate_signals(lookback_minutes=lookback)
            
            return [TextContent(
                type="text",
                text=f"✅ {count}개의 매매 신호가 생성되었습니다.\n\n`get_trading_signals` 명령으로 확인하세요."
            )]
        
        elif name == "execute_pending_orders":
            count = execute_signals()
            
            return [TextContent(
                type="text",
                text=f"✅ {count}건의 주문이 실행되었습니다.\n\n`get_recent_trades` 명령으로 확인하세요."
            )]
        
        elif name == "get_trading_config":
            config = get_trading_config()
            
            result = f"""⚙️ **자동매매 설정**

🔄 자동매매: {'✅ 활성화' if config.is_enabled else '❌ 비활성화'}
📊 신호 임계값: {float(config.score_threshold):.1f}
📉 손절: -{float(config.stop_loss_pct):.1f}%
📈 익절: +{float(config.take_profit_pct):.1f}%
💰 종목당 최대: {float(config.max_position_size):,.0f}원
🔢 하루 최대 거래: {config.max_daily_trades}건
"""
            return [TextContent(type="text", text=result)]
        
        elif name == "toggle_auto_trading":
            enable = arguments["enable"]
            
            with SessionLocal() as session:
                config = session.execute(select(TradingConfig).limit(1)).scalar_one_or_none()
                if config:
                    config.is_enabled = enable
                    config.updated_at = datetime.utcnow()
                    session.commit()
                    
                    status = "시작되었습니다" if enable else "중지되었습니다"
                    return [TextContent(
                        type="text",
                        text=f"✅ 자동매매가 {status}!"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text="❌ 설정을 찾을 수 없습니다."
                    )]
        
        elif name == "get_performance":
            with SessionLocal() as session:
                # 체결된 매매 내역
                trades = session.execute(
                    select(Trade).where(Trade.status == "FILLED")
                ).scalars().all()
                
                # 실현손익 계산 (간단히)
                buy_amount = sum(t.total_amount for t in trades if t.trade_type == "BUY")
                sell_amount = sum(t.total_amount for t in trades if t.trade_type == "SELL")
                realized_pnl = sell_amount - (buy_amount if sell_amount > 0 else 0)
                
                # 미실현손익
                positions = session.execute(
                    select(Position).where(Position.quantity > 0)
                ).scalars().all()
                unrealized_pnl = sum(float(p.unrealized_pnl) for p in positions)
                
                # 승패
                buy_trades = [t for t in trades if t.trade_type == "BUY"]
                sell_trades = [t for t in trades if t.trade_type == "SELL"]
                win_count = sum(1 for t in sell_trades if t.price > 0)  # 간단히
                total_trades = len(sell_trades)
                win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
                
                result = f"""📊 **투자 성과**

💰 실현손익: {realized_pnl:+,.0f}원
💵 미실현손익: {unrealized_pnl:+,.0f}원
📈 총 손익: {(realized_pnl + unrealized_pnl):+,.0f}원

🎯 승률: {win_rate:.1f}% ({win_count}승 {total_trades - win_count}패)
🔄 총 거래: {len(trades)}건
📌 보유 종목: {len(positions)}개
"""
                return [TextContent(type="text", text=result)]
        
        else:
            return [TextContent(type="text", text=f"알 수 없는 명령: {name}")]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ 오류 발생: {str(e)}"
        )]


async def main():
    """MCP 서버 실행"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
