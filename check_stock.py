
import json
import os

file_path = r"c:\Project\CB_kis\data\all_stocks.json"

if not os.path.exists(file_path):
    print("File not found")
else:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        found = False
        if "KR" in data:
            for s in data['KR']:
                if "이원" in s['name'] or "088290" in s['code']:
                    print(f"FOUND: {s}")
                    found = True
                    break
        
        if not found:
            print("NOT FOUND. Total KR stocks:", len(data.get('KR', [])))
            # Try appending again if not found
            if "KR" in data:
                data['KR'].append({
                    "code": "088290",
                    "name": "이원컴포텍",
                    "market": "KQ",
                    "exchange": "KRX"
                })
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print("FORCED APPEND Done.")

    except Exception as e:
        print(f"Error: {e}")
