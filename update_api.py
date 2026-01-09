
import os

api_file = r"c:\Project\CB_kis\app\api.py"

new_code = """
# ========================================
# [ADDED BY GEMINI] Missing Trading APIs
# ========================================

# === 종목 검색 API ===
@app.get("/api/trading/search")
def api_trading_search(query: str, market: str = "KR"):
    "종목 검색 API"
    import json
    import os
    
    # 1. 파일에서 종목 DB 로드 시도
    stocks = []
    
    # 캐시된 종목 파일 확인 (현재 디렉토리 기준 상위/루트 등 확인)
    # c:\\Project\\CB_kis\\all_stocks.json
    stock_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "all_stocks.json")
    
    if not os.path.exists(stock_file):
        # 파일이 없으면 주요 종목만 반환
        fallback_stocks = [
            {"stock_code": "005930", "stock_name": "삼성전자", "exchange": "KRX"},
            {"stock_code": "000660", "stock_name": "SK하이닉스", "exchange": "KRX"},
            {"stock_code": "035420", "stock_name": "NAVER", "exchange": "KRX"},
            {"stock_code": "035720", "stock_name": "카카오", "exchange": "KRX"},
            {"stock_code": "005380", "stock_name": "현대차", "exchange": "KRX"},
            {"stock_code": "051910", "stock_name": "LG화학", "exchange": "KRX"},
            {"stock_code": "207940", "stock_name": "삼성바이오로직스", "exchange": "KRX"},
            {"stock_code": "000270", "stock_name": "기아", "exchange": "KRX"},
            {"stock_code": "068270", "stock_name": "셀트리온", "exchange": "KRX"},
            {"stock_code": "086520", "stock_name": "에코프로", "exchange": "KOSDAQ"},
            {"stock_code": "247540", "stock_name": "에코프로비엠", "exchange": "KOSDAQ"}
        ]
        
        # 검색 필터
        results = [s for s in fallback_stocks if query.upper() in s["stock_name"] or query in s["stock_code"]]
        return results

    try:
        with open(stock_file, "r", encoding="utf-8") as f:
            stocks = json.load(f)
            
        # 검색 로직
        results = []
        for s in stocks:
            if query.upper() in s.get("stock_name", "").upper() or query in s.get("stock_code", ""):
                results.append(s)
                if len(results) >= 10: break
                
        return results
    except Exception as e:
        print(f"검색 오류: {e}")
        return []

# === 미체결 내역 API (더미) ===
@app.get("/api/trading/orders")
def api_trading_orders():
    "미체결 내역 조회 (더미)"
    return [
        {
            "order_id": "1001",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "side": "매수",
            "price": 72000,
            "quantity": 10,
            "executed_qty": 0,
            "status": "접수",
            "time": "14:20:05"
        }
    ]

# === 거래 내역 API (더미) ===
@app.get("/api/trading/history")
def api_trading_history():
    "거래 내역 조회 (더미)"
    return [
        {
            "id": "2001",
            "stock_name": "SK하이닉스",
            "side": "매수",
            "price": 135000,
            "quantity": 5,
            "amount": 675000,
            "time": "2026-01-09 10:00:00"
        },
        {
            "id": "2002",
            "stock_name": "NAVER",
            "side": "매도",
            "price": 210000,
            "quantity": 2,
            "amount": 420000,
            "time": "2026-01-08 15:30:00"
        }
    ]
"""

try:
    with open(api_file, "r", encoding="utf-8") as f:
        content = f.read()

    if "api_trading_search" not in content:
        with open(api_file, "a", encoding="utf-8") as f:
            f.write(new_code)
        print("Successfully appended new APIs.")
    else:
        print("APIs already exist.")

except Exception as e:
    print(f"Error: {e}")
