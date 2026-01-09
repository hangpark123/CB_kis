
file_paths = [
    r"c:\Project\CB_kis\data\kospi_code.mst",
    r"c:\Project\CB_kis\data\kosdaq_code.mst"
]
target = "이원컴".encode("cp949")

for fp in file_paths:
    print(f"Scanning {fp}...")
    try:
        with open(fp, 'rb') as f:
            content = f.read()
            idx = content.find(target)
            if idx != -1:
                print(f"FOUND in {fp} at {idx}")
                start = max(0, idx - 50)
                end = min(len(content), idx + 100)
                chunk = content[start:end]
                print(f"Chunk raw: {chunk}")
                try:
                    print(f"Chunk decoded: {chunk.decode('cp949', errors='ignore')}")
                except: pass
            else:
                print("Not found")
    except Exception as e:
        print(e)
