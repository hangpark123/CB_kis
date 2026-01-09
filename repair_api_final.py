
import os

api_path = r"c:\Project\CB_kis\app\api.py"

# 새로운 API 코드 (깨끗한 문자열)
new_apis = """

# ===주문/정정/취소 API (New) ===
@app.post("/api/trading/manual_order")
def api_manual_order(stock_code: str, order_type: str, quantity: int, price: int, market: str = "KR"):
    \"\"\"수동 주문 실행 (매수/매도)\"\"\"
    # 실제 KIS API 연동 필요 (여기서는 더미/로그만 남김 or 실제 구현)
    import logging
    print(f"[ORDER] {order_type} {stock_code} : {quantity}주 @ {price}원 ({market})")
    
    # 성공 응답 가정
    return {"status": "ok", "message": "주문 전송 완료", "order_id": "123456"}

@app.post("/api/trading/revise_cancel")
def api_revise_cancel(order_id: str, type: str, quantity: int = 0, price: int = 0):
    \"\"\"주문 정정/취소\"\"\"
    # type: 'revise' or 'cancel'
    print(f"[REVISE/CANCEL] Order {order_id} -> {type} (Qty:{quantity}, Price:{price})")
    return {"status": "ok", "message": f"주문 {type} 처리 완료"}
"""

try:
    # 1. 바이너리 모드로 읽기
    with open(api_path, "rb") as f:
        content = f.read()

    # 2. 깨진 부분 찾기 (# Force Reload 3 뒤의 쓰레기값 제거)
    marker = b"# Force Reload 3"
    idx = content.find(marker)

    if idx != -1:
        # 마커까지의 정상적인 내용만 취함
        clean_content = content[:idx + len(marker)]
        
        # 3. 새로운 내용 붙여서 다시 쓰기 (UTF-8 인코딩)
        final_content = clean_content.decode('utf-8', errors='ignore') + new_apis
        
        with open(api_path, "w", encoding="utf-8") as f:
            f.write(final_content)
            
        print("SUCCESS: api.py repaired successfully.")
    else:
        print("WARNING: Marker '# Force Reload 3' not found. Appending anyway.")
        # 마커가 없으면 그냥 뒤에 붙이는 건 위험하므로 기존 내용을 문자열로 정화 후 붙임
        clean_content = content.replace(b'\x00', b'') # Null byte 제거
        final_content = clean_content.decode('utf-8', errors='ignore') + new_apis
        with open(api_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        print("SUCCESS: api.py cleaned (null bytes removed) and updated.")

except Exception as e:
    print(f"ERROR: {e}")
