
import httpx
import re
import json
import os
import time

def scrape_market(market_code):
    # 0: KOSPI, 1: KOSDAQ
    base_url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={market_code}&page="
    stocks = []
    page = 1
    
    print(f"Scraping Market {market_code}...")
    
    while True:
        try:
            url = base_url + str(page)
            print(f"  Page {page}...", end='\r')
            
            resp = httpx.get(url, timeout=10.0)
            if resp.status_code != 200:
                break
                
            html = resp.content.decode('euc-kr', errors='ignore')
            
            # 파싱: <a href="/item/main.naver?code=XXXXXX" class="tltle">이름</a>
            # Regex로 추출
            items = re.findall(r'<a href="/item/main.naver\?code=(\d{6})"[^>]*>([^<]+)</a>', html)
            
            if not items:
                break
                
            for code, name in items:
                stocks.append({
                    "code": code,
                    "name": name,
                    "market": "KR",
                    "exchange": "KRX" # Unified for simplicity
                })
                
            # 페이지 끝 확인 (마지막 페이지 반복됨) -> 네이버는 페이지 넘어가도 내용 없으면 items가 없음.
            # 하지만 네이버 금융은 페이지 넘어가도 마지막 페이지 내용을 보여주는 경우가 있음.
            # "다음" 버튼 유무로 체크하거나, items가 이전 페이지와 동일하면 break.
            
            page += 1
            if page > 40: # Safety break (KOSDAQ is around 32 pages)
                break
                
            time.sleep(0.1) # Be nice
            
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
            
    print(f"  Done. Found {len(stocks)} stocks.")
    return stocks

def main():
    kospi = scrape_market(0)
    kosdaq = scrape_market(1)
    
    all_kr = kospi + kosdaq
    
    # Load existing to keep US stocks
    file_path = r"c:\Project\CB_kis\data\all_stocks.json"
    data = {"KR": [], "US": []}
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            data["US"] = existing.get("US", [])
            
    # Remove duplicates
    seen = set()
    unique_kr = []
    for s in all_kr:
        if s['code'] not in seen:
            seen.add(s['code'])
            unique_kr.append(s)
            
    data["KR"] = unique_kr
    
    # Ensure dir exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Saved {len(unique_kr)} KR stocks to {file_path}")

if __name__ == "__main__":
    main()
