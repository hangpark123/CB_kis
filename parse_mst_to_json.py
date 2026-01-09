
import os
import json

target_bytes = "이원컴".encode("cp949")

def parse_mst_file(file_path):
    stocks = []
    try:
        # CP949 인코딩으로 읽기
        with open(file_path, 'r', encoding='cp949') as f:
            lines = f.readlines()
            
        print(f"Parsing {os.path.basename(file_path)}: {len(lines)} lines")
        
        for line in lines:
            # 포맷 유추: 
            # 0~9: 단축코드 (9자리)
            # 9~21: 표준코드 (12자리)
            # 21~61: 한글명 (40자리) - 바이트 기준이라 인덱싱 주의 (Python은 문자 기준)
            # Python의 slice는 문자(Character) 단위이므로, 한글이 포함된 경우 byte offset과 다를 수 있음.
            # 따라서 파일을 'rb'로 읽어서 바이트 슬라이싱 후 디코딩하는 것이 안전함.
            pass

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    # Re-implement using binary read
    stocks = []
    try:
        with open(file_path, 'rb') as f:
            # 고정 길이인지 라인 구분인지 확인 필요. 아까 \n이 있었음.
            # 라인 단위로 읽되 바이트로 처리
            content = f.read()
            # \n (0x0a) 로 분리
            lines = content.split(b'\n')
            
            for line in lines:
                line = line.rstrip(b'\r')
                if len(line) < 61: continue # 최소한 이름까지는 있어야 함
                
                try:
                    # 필드 스펙 (바이트 기준)
                    # 단축코드: 0~9
                    # 표준코드: 9~21
                    # 한글명: 21~61 (40바이트)
                    
                    short_code = line[0:9].decode('cp949', errors='ignore').strip()
                    std_code = line[9:21].decode('cp949', errors='ignore').strip()
                    kor_name = line[21:61].decode('cp949', errors='ignore').strip()
                    
                    if not short_code or not kor_name: continue
                    
                    if "088290" in short_code:
                        raw_name = line[21:61]
                        print(f"DEBUG Name Repr: {repr(kor_name)}")

                    stocks.append({
                        "code": short_code,
                        "name": kor_name,
                        "market_type": "KOSDAQ" if "kosdaq" in file_path.lower() else "KOSPI"
                    })
                except Exception as line_e:
                    # 그래도 에러나면 스킵
                    continue
                    
    except Exception as e:
        print(f"Error parsing binary {file_path}: {e}")
        
    return stocks

def main():
    base_dir = r"c:\Project\CB_kis\data"
    kospi_file = os.path.join(base_dir, "kospi_code.mst")
    kosdaq_file = os.path.join(base_dir, "kosdaq_code.mst")
    
    kospi_stocks = parse_mst_file(kospi_file)
    kosdaq_stocks = parse_mst_file(kosdaq_file)
    
    print(f"KOSPI: {len(kospi_stocks)}")
    print(f"KOSDAQ: {len(kosdaq_stocks)}")
    
    all_kr = kospi_stocks + kosdaq_stocks
    
    # Load exisiting json
    json_path = os.path.join(base_dir, "all_stocks.json")
    data = {"KR": [], "US": []}
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                if isinstance(existing, dict):
                    data["US"] = existing.get("US", [])
                # 만약 리스트 구조였다면 기존 데이터 무시하고 새로 씀 (KR 갱신)
        except:
            pass
            
    # Format for JSON
    # api.py expects: code, name, market, exchange
    formatted_kr = []
    for s in all_kr:
        formatted_kr.append({
            "code": s['code'],
            "name": s['name'],
            "market": "KR",
            "exchange": "KRX" # Unified
        })
        
    data["KR"] = formatted_kr
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Saved {len(formatted_kr)} stocks to all_stocks.json")

if __name__ == "__main__":
    main()
