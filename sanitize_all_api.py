
import os

api_path = r"c:\Project\CB_kis\app\api.py"

print(f"Sanitizing {api_path}...")

try:
    with open(api_path, "rb") as f:
        content = f.read()

    original_len = len(content)
    # Remove all null bytes
    cleaned = content.replace(b'\x00', b'')
    new_len = len(cleaned)

    if original_len != new_len:
        print(f"Detected {original_len - new_len} null bytes. Removing them.")
        with open(api_path, "wb") as f:
            f.write(cleaned)
        print("File rewritten.")
    else:
        print("No null bytes found. The file might be clean, or the issue is elsewhere.")

except Exception as e:
    print(f"Error: {e}")
