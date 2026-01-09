"""
KIS 종목정보 마스터 파일 파싱 및 통합
data/ 폴더 내으 .mst (한국) 및 .cod (미국) 파일을 파싱하여 all_stocks.json 생성
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

def parse_us_cod_file(file_path: Path):
    """미국 주식 COD 파일 파싱 (탭 구분자)"""
    stocks = []
    print(f"[{file_path.name}] 파싱 중...")
    
    try:
        # cp949 인코딩으로 읽기
        content = file_path.read_text(encoding='cp949', errors='ignore')
        lines = content.split('\n')
        
        for line in lines:
            parts = line.split('\t')
            if len(parts) < 8:
                continue
            
            # 인덱스 추정:
            # 0:국가, 1:?, 2:거래소코드, 3:한글거래소명, 4:심볼, 5:표준코드, 6:한글명, 7:영문명
            symbol = parts[4].strip()
            name_kr = parts[6].strip()
            name_en = parts[7].strip()
            
            # 거래소 확인 (파일명 또는 내부 코드)
            exchange = "NASDAQ" if "NAS" in file_path.name else "NYSE"
            if "AMS" in file_path.name: 
                exchange = "AMEX"
            
            if symbol and name_en:
                stock = {
                    "code": symbol,
                    "name": name_en,
                    "name_kr": name_kr,
                    "exchange": exchange,
                    "market": "US"
                }
                stocks.append(stock)
                
        print(f"  > {len(stocks)}개 종목 추출")
        return stocks
        
    except Exception as e:
        print(f"  > 파싱 실패: {e}")
        return []

def parse_kr_mst_file(file_path: Path):
    """한국 주식 MST 파일 파싱 (고정폭)"""
    stocks = []
    print(f"[{file_path.name}] 파싱 중...")
    
    try:
        content = file_path.read_text(encoding='cp949', errors='ignore')
        lines = content.split('\n')
        
        for line in lines:
            # line 길이 체크 (최소 길이보다 짧으면 스킵)
            if len(line) < 50:
                continue
                
            # 고정폭 포맷 (바이트 단위여야 정확하지만, cp949 디코딩 후에는 문자 단위로 접근)
            # 단축코드(9) | 표준코드(12) | 한글명(40?) ...
            # python string slice는 문자 단위임.
            # 하지만 MST 파일은 바이트 offset 기준이므로, 한글이 섞이면 인덱스가 밀릴 수 있음.
            # 정확히 하려면 바이트로 읽어서 잘라야 함.
            
            # 간단한 방법: 바이트로 다시 인코딩해서 자르기? 너무 느림.
            # 그냥 문자열 슬라이싱 시도 (대략적인 위치)
            
            # 단축코드: 앞 9자리 (보통 6자리 + 공백)
            code = line[0:9].strip()
            
            # 한글명: 21번째부터 40바이트 (추정)
            # 샘플: "000020동화약품                                ST30"
            # 이름 뒤에 공백이 길게 있고 그 뒤에 다른 코드가 있음.
            # 21번째부터 넉넉하게 자른 뒤, 연속된 공백 2개 이상("  ")이 나오면 그 앞까지만 사용
            
            raw_name = line[21:80] # 넉넉하게 가져옴
            
            # 1. 연속된 공백 2개 이상으로 분리 -> 첫 번째 덩어리가 이름일 확률 높음
            parts = raw_name.split('  ')
            name_part = parts[0].strip()
            
            # 혹시 이름이 비어있으면(공백이 없었던 경우), strip만 사용
            if not name_part:
                name_part = raw_name.strip()
            
            # 유효성 검사 (코드가 숫자 + 문자 등 6자리 이상)
            if len(code) >= 6:
                stock = {
                    "code": code,
                    "name": name_part, # 한국 주식은 이게 종목명
                    "market": "KR",
                    "exchange": "KOSDAQ" if "kosdaq" in file_path.name.lower() else "KOSPI"
                }
                stocks.append(stock)

        print(f"  > {len(stocks)}개 종목 추출")
        return stocks

    except Exception as e:
        print(f"  > 파싱 실패: {e}")
        return []

def main():
    print("=== 마스터 파일 파싱 및 통합 DB 생성 ===\n")
    
    all_stocks_kr = []
    all_stocks_us = []
    
    # 1. 한국 주식 (kospi_code.mst, kosdaq_code.mst)
    mst_files = list(DATA_DIR.glob("*.mst"))
    for f in mst_files:
        stocks = parse_kr_mst_file(f)
        all_stocks_kr.extend(stocks)
        
    # 2. 미국 주식 (*.COD)
    cod_files = list(DATA_DIR.glob("*.COD"))
    for f in cod_files:
        stocks = parse_us_cod_file(f)
        all_stocks_us.extend(stocks)
        
    # 중복 제거 (심볼 기준)
    unique_us = {s['code']: s for s in all_stocks_us}
    all_stocks_us = list(unique_us.values())
    all_stocks_us.sort(key=lambda x: x['code'])
    
    unique_kr = {s['code']: s for s in all_stocks_kr}
    all_stocks_kr = list(unique_kr.values())
    all_stocks_kr.sort(key=lambda x: x['code'])
    
    # 통합 저장
    data = {
        "KR": all_stocks_kr,
        "US": all_stocks_us
    }
    
    save_path = DATA_DIR / "all_stocks.json"
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"\n[OK] 완료! 저장 위치: {save_path}")
    print(f"  KR: {len(all_stocks_kr)}개 (전종목)")
    print(f"  US: {len(all_stocks_us)}개 (전종목 + 한글명)")
    
    print("\n[SAMPLE US] 미국 주식 샘플:")
    for s in all_stocks_us[:5]:
        print(f"  {s['code']:8} {s['name_kr']} ({s['name']})")
        
    print("\n[SAMPLE KR] 한국 주식 샘플:")
    for s in all_stocks_kr[:5]:
        print(f"  {s['code']:8} {s['name']}")

if __name__ == "__main__":
    main()
