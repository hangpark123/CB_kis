
import os

api_path = r"c:\Project\CB_kis\app\api.py"
append_path = r"c:\Project\CB_kis\append_apis.py"

# Read API file (binary mode to handle garbage)
with open(api_path, "rb") as f:
    content = f.read()

# Find the marker
marker = b"# Force Reload 3"
idx = content.find(marker)

if idx != -1:
    # Keep content up to marker + newline
    # Assuming \r\n or \n follows
    end_idx = content.find(b"\n", idx)
    if end_idx != -1:
        clean_content = content[:end_idx+1]
    else:
        clean_content = content[:idx + len(marker)]
else:
    print("Marker not found, creating backup and rewriting")
    clean_content = content # Fallback, but risky if marker missing

# Read append file
with open(append_path, "rb") as f:
    append_data = f.read()

# Write merged
with open(api_path, "wb") as f:
    f.write(clean_content)
    f.write(b"\n\n")
    f.write(append_data)

print("Fixed api.py")
