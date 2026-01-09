"""
나스닥/NYSE 전체 종목 다운로드 (HTTP 버전)
GitHub에서 제공하는 종목 리스트 사용
"""

import httpx
import json
from pathlib import Path

# GitHub 공개 데이터 소스
NASDAQ_URL = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_full_tickers.json"
NYSE_URL = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nyse/nyse_full_tickers.json"

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def download_stocks(url, exchange):
    """주식 리스트 다운로드"""
    print(f"[{exchange}] 다운로드 중...")
    
    try:
        response = httpx.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        
        data = response.json()
        stocks = []
        
        for item in data:
            symbol = item.get('symbol', '')
            name = item.get('name', symbol)
            
            if symbol:
                stocks.append({
                    "code": symbol,
                    "name": name,
                    "exchange": exchange
                })
        
        print(f"[OK] {exchange}: {len(stocks)}개 종목")
        return stocks
    
    except Exception as e:
        print(f"[ERROR] {exchange} 다운로드 실패: {e}")
        return []


def main():
    """전체 미국 주식 종목 다운로드"""
    print("=" * 50)
    print("[US] 미국 주식 전체 종목 다운로드")
    print("=" * 50)
    print()
    
    # 나스닥 + NYSE
    nasdaq_stocks = download_stocks(NASDAQ_URL, "NASDAQ")
    nyse_stocks = download_stocks(NYSE_URL, "NYSE")
    
    all_stocks = nasdaq_stocks + nyse_stocks
    
    # 중복 제거
    unique_stocks = {}
    for stock in all_stocks:
        code = stock['code']
        if code not in unique_stocks:
            unique_stocks[code] = stock
    
    final_stocks = list(unique_stocks.values())
    final_stocks.sort(key=lambda x: x['code'])
    
    # JSON 저장
    json_path = DATA_DIR / "us_stocks.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({"US": final_stocks}, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 50)
    print(f"[OK] 완료! 총 {len(final_stocks)}개 종목")
    print(f"[FILE] 저장: {json_path}")
    print("=" * 50)
    print()
    
    # 샘플
    print("[SAMPLE] 처음 30개:")
    for stock in final_stocks[:30]:
        print(f"  {stock['code']:10} {stock['name'][:50]:50} ({stock['exchange']})")
    
    print()
    print(f"[INFO] 전체 {len(final_stocks)}개 종목 검색 가능!")


if __name__ == "__main__":
    main()
