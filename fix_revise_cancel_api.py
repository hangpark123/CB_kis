#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
api.py의 주문 취소 API 부분을 수정하는 스크립트
"""

# 파일 읽기
with open(r'c:\Project\CB_kis\app\api.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# 주문 취소 API 부분 찾아서 교체
old_code = '''@app.post("/api/trading/revise_cancel")

def api_revise_cancel(order_id: str, type: str, quantity: int = 0, price: int = 0):

    """주문 정정/취소"""

    # type: 'revise' or 'cancel'

    print(f"[REVISE/CANCEL] Order {order_id} -> {type} (Qty:{quantity}, Price:{price})")

    return {"status": "ok", "message": f"주문 {type} 완료"}'''

new_code = '''@app.post("/api/trading/revise_cancel")
def api_revise_cancel(order_id: str, type: str, quantity: int = 0, price: int = 0):
    """주문 취소/정정"""
    from .kis_api import cancel_order
    
    try:
        if type == "cancel":
            result = cancel_order(order_id)
            if result.get("status") == "ok":
                return {"status": "ok", "message": "주문 취소 완료"}
            else:
                return {"status": "error", "message": result.get("message", "취소 실패")}
        else:
            # 정정 기능은 추후 구현
            return {"status": "error", "message": "정정 기능은 아직 지원되지 않습니다"}
    except Exception as e:
        print(f"주문 취소 오류: {e}")
        return {"status": "error", "message": str(e)}'''

# 교체 수행
if old_code in content:
    content = content.replace(old_code, new_code)
    print("주문 취소 API 코드를 찾아서 교체했습니다.")
else:
    # 대안: 패턴 매칭으로 찾기
    import re
    pattern = r'@app\.post\("/api/trading/revise_cancel"\).*?return \{"status".*?완료"\}'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = content[:match.start()] + new_code + content[match.end():]
        print("정규식 패턴으로 주문 취소 API 코드를 교체했습니다.")
    else:
        print("경고: 주문 취소 API 코드를 찾을 수 없습니다. 파일 끝에 추가합니다.")
        # 맨 끝에 추가
        content = content.rstrip() + '\n\n' + new_code + '\n'

# 파일 쓰기
with open(r'c:\Project\CB_kis\app\api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("api.py 파일 수정 완료!")
