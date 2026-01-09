"""
KIS 해외주식 API 함수
"""

import httpx
from typing import Optional, Dict, List
from .kis_auth import (
    KIS_BASE_URL,
    get_api_headers,
    get_account_info,
    get_hashkey
)


def _get_tr_id_overseas(real_tr_id: str) -> str:
    """해외주식 환경별 TR ID 반환"""
    if "vts" in KIS_BASE_URL or "openapivts" in KIS_BASE_URL:
        # 모의투자
        if real_tr_id.startswith("J"):
            return "T" + real_tr_id[1:]  # JTTT -> TTTT
    return real_tr_id


def get_us_stock_price(symbol: str, exchange: str = "NAS") -> Optional[Dict]:
    """
    미국 주식 현재가 조회
    
    Args:
        symbol: 티커 심볼 (예: "AAPL", "TSLA")
        exchange: 거래소 코드 (NAS=나스닥, NYS=뉴욕, AMS=아멕스)
    
    Returns:
        dict: {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "current_price": 150.25,
            "change_rate": 1.5,
            "currency": "USD"
        }
    """
    url = f"{KIS_BASE_URL}/uapi/overseas-price/v1/quotations/price"
    tr_id = "HHDFS00000300"  # 해외주식 현재가
    headers = get_api_headers(tr_id)
    
    params = {
        "AUTH": "",
        "EXCD": exchange,  # 거래소 코드
        "SYMB": symbol     # 심볼
    }
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        if data.get("rt_cd") != "0":
            print(f"API 오류: {data.get('msg1', 'Unknown')}")
            return None
        
        output = data.get("output", {})
        
        return {
            "symbol": symbol,
            "name": output.get("name", symbol),
            "current_price": float(output.get("last", 0)),
            "change_rate": float(output.get("rate", 0)),
            "volume": int(output.get("tvol", 0)),
            "currency": "USD"
        }
    
    except Exception as e:
        print(f"미국 주식 시세 조회 실패: {e}")
        return None


def get_us_balance() -> Dict:
    """
    해외주식 잔고 조회
    
    Returns:
        dict: {
            "cash_usd": 10000.00,  # 달러 예수금
            "total_value_usd": 15000.00,  # 총 평가금액(달러)
            "positions": [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "quantity": 10,
                    "avg_price": 145.0,
                    "current_price": 150.25,
                    "pnl_usd": 52.5,
                    "pnl_rate": 3.62
                }
            ]
        }
    """
    account = get_account_info()
    url = f"{KIS_BASE_URL}/uapi/overseas-stock/v1/trading/inquire-balance"
    
    # 모의투자: TTTS3012R, 실전: JTTT3012R
    tr_id = _get_tr_id_overseas("JTTT3012R")
    headers = get_api_headers(tr_id)
    
    params = {
        "CANO": account["account_no"],
        "ACNT_PRDT_CD": account["product_code"],
        "OVRS_EXCG_CD": "NASD",  # 나스닥 (NYS=뉴욕, HKS=홍콩 등)
        "TR_CRCY_CD": "USD",     # 통화
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        if data.get("rt_cd") != "0":
            print(f"API 오류: {data.get('msg1', 'Unknown')}")
            return {"cash_usd": 0, "total_value_usd": 0, "positions": []}
        
        output1 = data.get("output1", [])
        output2 = data.get("output2", [{}])[0]
        
        positions = []
        for item in output1:
            if float(item.get("ovrs_cblc_qty", 0)) > 0:  # 잔고수량
                positions.append({
                    "symbol": item.get("ovrs_pdno", ""),
                    "name": item.get("ovrs_item_name", ""),
                    "quantity": float(item.get("ovrs_cblc_qty", 0)),
                    "avg_price": float(item.get("pchs_avg_pric", 0)),
                    "current_price": float(item.get("now_pric2", 0)),
                    "pnl_usd": float(item.get("frcr_evlu_pfls_amt", 0)),
                    "pnl_rate": float(item.get("evlu_pfls_rt", 0))
                })
        
        return {
            "cash_usd": float(output2.get("frcr_dncl_amt_2", 0)),  # 외화예수금
            "total_value_usd": float(output2.get("tot_evlu_pfls_amt", 0)),  # 총평가금액
            "positions": positions
        }
    
    except Exception as e:
        print(f"해외주식 잔고 조회 실패: {e}")
        return {"cash_usd": 0, "total_value_usd": 0, "positions": []}


def order_us_buy(symbol: str, quantity: int, exchange: str = "NAS", price: Optional[float] = None) -> Optional[str]:
    """
    미국 주식 매수
    
    Args:
        symbol: 티커 심볼
        quantity: 수량
        exchange: 거래소 (NAS, NYS 등)
        price: 지정가 (None이면 시장가)
    
    Returns:
        주문번호 or None
    """
    account = get_account_info()
    url = f"{KIS_BASE_URL}/uapi/overseas-stock/v1/trading/order"
    
    # 모의투자: TTTT1002U, 실전: JTTT1002U
    tr_id = _get_tr_id_overseas("JTTT1002U")
    
    order_data = {
        "CANO": account["account_no"],
        "ACNT_PRDT_CD": account["product_code"],
        "OVRS_EXCG_CD": exchange,
        "PDNO": symbol,
        "ORD_QTY": str(quantity),
        "OVRS_ORD_UNPR": str(price) if price else "0",
        "ORD_SVR_DVSN_CD": "0",  # 0=지점, 1=온라인
        "ORD_DVSN": "00" if not price else "01"  # 00=시장가, 01=지정가
    }
    
    headers = get_api_headers(tr_id)
    headers["hashkey"] = get_hashkey(order_data)
    
    try:
        response = httpx.post(url, headers=headers, json=order_data, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        if data.get("rt_cd") == "0":
            order_no = data.get("output", {}).get("ODNO", "")
            print(f"✅ 미국 주식 매수 성공: {symbol} {quantity}주, 주문번호 {order_no}")
            return order_no
        else:
            print(f"❌ 주문 실패: {data.get('msg1', 'Unknown')}")
            return None
    
    except Exception as e:
        print(f"주문 실패: {e}")
        return None


def order_us_sell(symbol: str, quantity: int, exchange: str = "NAS", price: Optional[float] = None) -> Optional[str]:
    """
    미국 주식 매도
    
    Args:
        symbol: 티커 심볼
        quantity: 수량
        exchange: 거래소
        price: 지정가 (None이면 시장가)
    
    Returns:
        주문번호 or None
    """
    account = get_account_info()
    url = f"{KIS_BASE_URL}/uapi/overseas-stock/v1/trading/order"
    
    # 모의투자: TTTT1006U, 실전: JTTT1006U
    tr_id = _get_tr_id_overseas("JTTT1006U")
    
    order_data = {
        "CANO": account["account_no"],
        "ACNT_PRDT_CD": account["product_code"],
        "OVRS_EXCG_CD": exchange,
        "PDNO": symbol,
        "ORD_QTY": str(quantity),
        "OVRS_ORD_UNPR": str(price) if price else "0",
        "ORD_SVR_DVSN_CD": "0",
        "ORD_DVSN": "00" if not price else "01"
    }
    
    headers = get_api_headers(tr_id)
    headers["hashkey"] = get_hashkey(order_data)
    
    try:
        response = httpx.post(url, headers=headers, json=order_data, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        if data.get("rt_cd") == "0":
            order_no = data.get("output", {}).get("ODNO", "")
            print(f"✅ 미국 주식 매도 성공: {symbol} {quantity}주, 주문번호 {order_no}")
            return order_no
        else:
            print(f"❌ 주문 실패: {data.get('msg1', 'Unknown')}")
            return None
    
    except Exception as e:
        print(f"주문 실패: {e}")
        return None


# 테스트
if __name__ == "__main__":
    print("=== 미국 주식 API 테스트 ===")
    
    # 현재가 조회
    print("\n1. Apple 현재가 조회")
    price_info = get_us_stock_price("AAPL", "NAS")
    if price_info:
        print(f"   {price_info}")
    
    # 잔고 조회
    print("\n2. 미국 주식 잔고 조회")
    balance = get_us_balance()
    print(f"   예수금: ${balance['cash_usd']:,.2f}")
    print(f"   총 평가: ${balance['total_value_usd']:,.2f}")
    print(f"   보유 종목: {len(balance['positions'])}개")
    for p in balance['positions']:
        print(f"     - {p['symbol']}: {p['quantity']}주 @ ${p['current_price']:.2f}")
