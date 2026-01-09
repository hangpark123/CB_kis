
import os
import os
import httpx
from app.kis_auth import get_access_token, KIS_APPKEY, KIS_APPSECRET, KIS_ACCOUNT_NO, KIS_ACCOUNT_PROD, KIS_BASE_URL

# Alias for compatibility if needed, but better use correct names
KIS_CANO = KIS_ACCOUNT_NO
KIS_ACNT_PRDT_CD = KIS_ACCOUNT_PROD

def debug_order_possible():
    token = get_access_token()
    
    # Check if Mock or Real
    is_mock = "vts" in KIS_BASE_URL
    tr_id = "VTTC8908R" if is_mock else "TTTC8908R"
    
    print(f"DEBUG: Base URL: {KIS_BASE_URL}")
    print(f"DEBUG: TR ID: {tr_id}")
    
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": KIS_APPKEY,
        "appsecret": KIS_APPSECRET,
        "tr_id": tr_id
    }
    
    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/trading/inquire-psbl-order"
    
    # Test with Samsung Electronics (005930)
    params = {
        "CANO": KIS_CANO,
        "ACNT_PRDT_CD": KIS_ACNT_PRDT_CD,
        "PDNO": "005930", 
        "ORD_UNPR": "0", 
        "ORD_DVSN": "01", # Market Price
        "CMA_EVLU_AMT_ICLD_YN": "Y", 
        "OVRS_ICLD_YN": "N"
    }
    
    print("Sending Request...")
    try:
        resp = httpx.get(url, headers=headers, params=params, timeout=10.0)
        data = resp.json()
        print(f"Status Code: {resp.status_code}")
        print("Response Body:")
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_order_possible()
