# -*- coding: utf-8 -*-
"""
KIS API 래퍼 (간소화 버전)
차트 데이터는 Yahoo Finance 사용
"""

from typing import Dict, Optional
import httpx
import time
from .kis_auth import (
    get_api_headers,
    get_account_info,
    get_hashkey,
    KIS_BASE_URL
)

# Rate Limiting & Cache
_last_api_call_time = 0
_min_interval = 2.0
_cache = {}
_cache_ttl = 10

def _wait_for_rate_limit():
    """API 호출 간 최소 간격 보장"""
    global _last_api_call_time
    current_time = time.time()
    elapsed = current_time - _last_api_call_time
    
    if elapsed < _min_interval:
        wait_time = _min_interval - elapsed
        time.sleep(wait_time)
    
    _last_api_call_time = time.time()

def _get_cached(key):
    """캐시에서 데이터 가져오기"""
    if key in _cache:
        data, timestamp = _cache[key]
        if time.time() - timestamp < _cache_ttl:
            return data
    return None

def _set_cache(key, data):
    """캐시에 데이터 저장"""
    _cache[key] = (data, time.time())

# TR ID 변환
def _is_mock_env():
    """모의투자 환경 여부 확인"""
    return "vts" in KIS_BASE_URL or "29443" in KIS_BASE_URL

def _get_tr_id(tr_id: str) -> str:
    """모의투자/실전투자 TR ID 자동 변환"""
    if _is_mock_env():
        if tr_id == "TTTC8434R":  # 주식 잔고 조회
            return "VTTC8434R"
        elif tr_id == "TTTC0802U":  # 주식 매수
            return "VTTC0802U"
        elif tr_id == "TTTC0801U":  # 주식 매도
            return "VTTC0801U"
        elif tr_id.startswith("T"): # 다른 T로 시작하는 TR ID도 V로 변환 시도
            return "V" + tr_id[1:]
            
    return tr_id


def get_current_price(stock_code: str) -> Optional[Dict]:
    """현재가 조회 (KIS API)"""
    cache_key = f"price_{stock_code}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached
    
    _wait_for_rate_limit()
    
    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = get_api_headers("FHKST01010100")
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": stock_code
    }
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        if data.get("rt_cd") != "0":
            print(f"[ERROR] 현재가 조회 실패: {data.get('msg1')}")
            return None
        
        output = data.get("output", {})
        
        result = {
            "stock_code": stock_code,
            "stock_name": output.get("prdt_name", ""),
            "current_price": int(output.get("stck_prpr", 0)),
            "change_rate": float(output.get("prdy_ctrt", 0)),
            "volume": int(output.get("acml_vol", 0))
        }
        
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        print(f"현재가 조회 실패 ({stock_code}): {e}")
        return None


def get_balance() -> Dict:
    """잔고 조회 (KIS API)"""
    cached = _get_cached("balance")
    if cached is not None:
        return cached
    
    _wait_for_rate_limit()
    
    account = get_account_info()
    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance"
    headers = get_api_headers(_get_tr_id("TTTC8434R"))
    
    params = {
        "CANO": account['account_no'],
        "ACNT_PRDT_CD": account['product_code'],
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=10.0)
        
        if response.status_code != 200:
            print(f"[ERROR] 잔고 조회 실패: HTTP {response.status_code}")
            return {"cash": 0, "total_value": 0, "positions": []}
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            print(f"[ERROR] 잔고 조회 API 오류: {data.get('msg1')}")
            return {"cash": 0, "total_value": 0, "positions": []}
        
        output1 = data.get("output1", [])
        output2 = data.get("output2", [{}])[0]
        
        positions = []
        for item in output1:
            if int(float(item.get("hldg_qty", 0))) > 0:
                positions.append({
                    "stock_code": item.get("pdno", ""),
                    "stock_name": item.get("prdt_name", ""),
                    "quantity": int(float(item.get("hldg_qty", 0))),
                    "avg_price": int(float(item.get("pchs_avg_pric", 0))),
                    "current_price": int(float(item.get("prpr", 0))),
                    "pnl": int(float(item.get("evlu_pfls_amt", 0))),
                    "pnl_rate": float(item.get("evlu_pfls_rt", 0))
                })
        
        result = {
            "cash": int(float(output2.get("dnca_tot_amt", 0))),
            "total_value": int(float(output2.get("tot_evlu_amt", 0))),
            "pnl": int(float(output2.get("evlu_pfls_smtl_amt", 0))),
            "positions": positions
        }
        
        _set_cache("balance", result)
        return result
        
    except Exception as e:
        print(f"잔고 조회 실패: {e}")
        return {"cash": 0, "total_value": 0, "positions": []}



def order_stock(stock_code: str, order_type: str, quantity: int, price: int = 0) -> dict:
    """주식 주문 (매수/매도)"""
    _wait_for_rate_limit()
    
    try:
        account = get_account_info()
        
        # 매수/매도 TR ID 결정
        is_buy = order_type.upper() == "BUY"
        tr_id = "TTTC0802U" if is_buy else "TTTC0801U"
        tr_id = _get_tr_id(tr_id)
        
        # 주문 구분 (00: 지정가, 01: 시장가)
        ord_dvsn = "00" if price > 0 else "01"
        
        data = {
            "CANO": account['account_no'],
            "ACNT_PRDT_CD": account['product_code'],
            "PDNO": stock_code,
            "ORD_DVSN": ord_dvsn,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price) if price > 0 else "0",
        }
        
        # Hashkey 생성
        hashkey = get_hashkey(data)
        
        # 헤더 생성
        headers = get_api_headers(tr_id, is_order=True, hashkey=hashkey)
        
        url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/trading/order-cash"
        
        response = httpx.post(url, headers=headers, json=data)
        result = response.json()
        
        if result.get("rt_cd") != "0":
            return {"status": "error", "message": result.get("msg1")}
            
        return {"status": "ok", "message": result.get("msg1"), "ord_no": result.get("output", {}).get("ODNO")}
        
    except Exception as e:
        print(f"주문 오류: {e}")
        return {"status": "error", "message": str(e)}


def get_daily_chart_data(stock_code: str, period_code: str = "D") -> list:
    """
    차트 데이터 조회 (Yahoo Finance)
    KIS API 대신 Yahoo Finance 사용으로 Rate Limit 회피
    """
    cache_key = f"chart_{stock_code}_{period_code}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached
    
    try:
        import yfinance as yf
        from datetime import datetime, timedelta
        
        # 한국 주식 심볼: 005930.KS (KOSPI) or .KQ (KOSDAQ)
        symbol = f"{stock_code}.KS"
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        
        # .KS 실패 시 .KQ 시도
        if hist.empty:
            symbol = f"{stock_code}.KQ"
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty:
            return []
        
        chart_data = []
        for date, row in hist.iterrows():
            chart_data.append({
                "time": date.strftime("%Y%m%d"),
                "open": int(row['Open']),
                "high": int(row['High']),
                "low": int(row['Low']),
                "close": int(row['Close']),
                "volume": int(row['Volume'])
            })
        
        print(f"[OK] {stock_code} 차트 ({len(chart_data)}개) - Yahoo Finance")
        
        _set_cache(cache_key, chart_data)
        return chart_data
        
    except Exception as e:
        print(f"차트 조회 오류 ({stock_code}): {e}")
        return []
