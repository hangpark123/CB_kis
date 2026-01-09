
file_path = r"c:\Project\CB_kis\data\kospi_code.mst"

try:
    with open(file_path, 'rb') as f:
        head = f.read(500)
        print("--- BINARY HEAD ---")
        print(head)
        try:
            print("--- DECODED (CP949) ---")
            print(head.decode('cp949', errors='ignore'))
        except:
            print("Decode failed")
except Exception as e:
    print(e)
