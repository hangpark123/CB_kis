
import json
import os

file_path = r"c:\Project\CB_kis\data\all_stocks.json"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check KR list
    if "KR" in data:
        if not any(s['code'] == '088290' for s in data['KR']):
            data['KR'].append({
                "code": "088290",
                "name": "이원컴포텍",
                "market": "KQ", # KOSDAQ
                "exchange": "KRX" # Important for compatibility
            })
            print("Added 이원컴포텍")
        else:
            print("Already exists")
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        print("KR key not found")
        
except Exception as e:
    print(f"Error: {e}")
