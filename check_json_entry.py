
import json

file_path = r"c:\Project\CB_kis\data\all_stocks.json"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    kr_stocks = data.get("KR", [])
    found = False
    for s in kr_stocks:
        if s['code'] == '088290':
            print(f"Found: {s}")
            print(f"Name repr: {repr(s['name'])}")
            found = True
            break
            
    if not found:
        print("Not found in JSON")

except Exception as e:
    print(e)
