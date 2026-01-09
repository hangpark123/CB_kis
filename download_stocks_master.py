"""
KIS 종목정보 마스터 파일 다운로드 및 JSON 변환
한국 주식 + 미국 주식 전체 종목 검색 지원
"""

import httpx
import json
from pathlib import Path

# 다운로드 URL (KIS Developers에서 확인)
URLS = {
    "KR_KOSPI": "https://new.real.download.dws.co.kr/common/master/kospi_code.mst",
    "KR_KOSDAQ": "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst",
    "US_NASDAQ": "https://new.real.download.dws.co.kr/common/master/nasmst.cod",
    "US_NYSE": "https://new.real.download.dws.co.kr/common/master/nysmst.cod",
}

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def download_master_file(market: str, url: str):
    """마스터 파일 다운로드"""
    print(f"[{market}] 다운로드 중...")
    
    try:
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()
        
        file_path = DATA_DIR / f"{market}.mst"
        file_path.write_bytes(response.content)
        
        print(f"[{market}] ✅ 저장: {file_path}")
        return file_path
    except Exception as e:
        print(f"[{market}] ❌ 실패: {e}")
        return None


def parse_kr_master(file_path: Path):
    """한국 주식 마스터 파일 파싱"""
    stocks = []
    
    try:
        # 한국 주식 마스터 파일 형식 (Fixed Width)
        # 종목코드(9) | 종목명(40) | ...
        content = file_path.read_text(encoding='cp949', errors='ignore')
        
        for line in content.split('\n'):
            if len(line) < 50:
                continue
            
            code = line[0:9].strip()
            name = line[9:49].strip()
            
            if code and name and code.isdigit() and len(code) == 6:
                stocks.append({
                    "code": code,
                    "name": name,
                    "market": "KR"
                })
        
        print(f"  파싱 완료: {len(stocks)}개 종목")
        return stocks
    
    except Exception as e:
        print(f"  파싱 실패: {e}")
        return []


def parse_us_master(file_path: Path, exchange: str):
    """미국 주식 마스터 파일 파싱"""
    stocks = []
    
    try:
        # 미국 주식 마스터 파일 형식
        content = file_path.read_text(encoding='cp949', errors='ignore')
        
        for line in content.split('\n'):
            if len(line) < 50:
                continue
            
            # 심볼(15) | 종목명(30) | ...
            symbol = line[0:15].strip()
            name = line[15:45].strip()
            
            if symbol and name:
                stocks.append({
                    "code": symbol,
                    "name": name,
                    "market": "US",
                    "exchange": exchange
                })
        
        print(f"  파싱 완료: {len(stocks)}개 종목")
        return stocks
    
    except Exception as e:
        print(f"  파싱 실패: {e}")
        return []


def main():
    """전체 마스터 파일 다운로드 및 JSON 생성"""
    print("=== KIS 종목정보 마스터 파일 다운로드 ===\n")
    
    all_stocks = []
    
    # 한국 주식
    for market_name, url in [("KR_KOSPI", URLS["KR_KOSPI"]), ("KR_KOSDAQ", URLS["KR_KOSDAQ"])]:
        file_path = download_master_file(market_name, url)
        if file_path:
            stocks = parse_kr_master(file_path)
            all_stocks.extend(stocks)
    
    # 미국 주식
    for market_name, url, exchange in [
        ("US_NASDAQ", URLS["US_NASDAQ"], "NASDAQ"),
        ("US_NYSE", URLS["US_NYSE"], "NYSE")
    ]:
        file_path = download_master_file(market_name, url)
        if file_path:
            stocks = parse_us_master(file_path, exchange)
            all_stocks.extend(stocks)
    
    # JSON 저장
    json_path = DATA_DIR / "stocks_master.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_stocks, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 완료! 총 {len(all_stocks)}개 종목")
    print(f"📁 저장 위치: {json_path}")
    
    # 샘플 출력
    print("\n📊 샘플:")
    for stock in all_stocks[:10]:
        print(f"  {stock['code']:10} {stock['name']:30} ({stock['market']})")


if __name__ == "__main__":
    main()
