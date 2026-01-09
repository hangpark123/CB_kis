
file_path = r"c:\Project\CB_kis\data\kospi_code.mst"
target = "삼성전자".encode("cp949")
target_code = "005930".encode("cp949")

try:
    with open(file_path, 'rb') as f:
        content = f.read()
        
        idx = content.find(target_code)
        if idx != -1:
            print(f"Code '005930' found at offset: {idx}")
            # Print surrounding
            start = max(0, idx - 20)
            end = min(len(content), idx + 200)
            chunk = content[start:end]
            print(f"Chunk (raw): {chunk}")
            try:
                print(f"Chunk (decoded): {chunk.decode('cp949', errors='ignore')}")
            except: pass
            
        else:
            print("Code not found")
            
except Exception as e:
    print(e)
