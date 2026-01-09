"""
한국투자증권 Open API 인증 모듈

환경변수(.env)에서 API 키를 읽고, 토큰을 발급/갱신하며,
API 호출에 필요한 헤더를 생성합니다.
"""

import os
import time
import json
import hashlib
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 환경변수에서 설정 로드
KIS_APPKEY = os.getenv("KIS_APPKEY", "").strip("'\"")
KIS_APPSECRET = os.getenv("KIS_APPSECRET", "").strip("'\"")
KIS_BASE_URL = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443")
KIS_ACCOUNT_NO = os.getenv("KIS_ACCOUNT_NO", "")
KIS_ACCOUNT_PROD = os.getenv("KIS_ACCOUNT_PROD", "01")

# 토큰 저장 경로 (프로젝트 루트/.tokens/)
TOKEN_DIR = Path(__file__).parent.parent / ".tokens"
TOKEN_DIR.mkdir(exist_ok=True)
TOKEN_FILE = TOKEN_DIR / "kis_token.json"

# 토큰 캐시
_token_cache = {
    "access_token": None,
    "expires_at": None
}


def _save_token(token: str, expires_in: int):
    """토큰을 파일에 저장"""
    expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 1분 여유
    data = {
        "access_token": token,
        "expires_at": expires_at.isoformat()
    }
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    
    _token_cache["access_token"] = token
    _token_cache["expires_at"] = expires_at


def _load_token():
    """저장된 토큰 로드"""
    if not TOKEN_FILE.exists():
        return None
    
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        expires_at = datetime.fromisoformat(data["expires_at"])
        if datetime.now() < expires_at:
            _token_cache["access_token"] = data["access_token"]
            _token_cache["expires_at"] = expires_at
            return data["access_token"]
    except Exception as e:
        print(f"토큰 로드 실패: {e}")
    
    return None


def get_access_token(force_refresh=False):
    """
    액세스 토큰 발급 또는 캐시된 토큰 반환
    
    Args:
        force_refresh: True면 강제로 새 토큰 발급
    
    Returns:
        str: 액세스 토큰
    """
    # 캐시 확인
    if not force_refresh:
        if _token_cache["access_token"] and _token_cache["expires_at"]:
            if datetime.now() < _token_cache["expires_at"]:
                return _token_cache["access_token"]
        
        # 파일에서 로드 시도
        token = _load_token()
        if token:
            return token
    
    # 새 토큰 발급
    url = f"{KIS_BASE_URL}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": KIS_APPKEY,
        "appsecret": KIS_APPSECRET
    }
    
    try:
        response = httpx.post(url, headers=headers, json=body, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        access_token = data["access_token"]
        expires_in = data.get("expires_in", 86400)  # 기본 24시간
        
        _save_token(access_token, expires_in)
        print(f"[OK] KIS 토큰 발급 성공 (만료: {_token_cache['expires_at']})")
        return access_token
    
    except Exception as e:
        raise Exception(f"KIS 토큰 발급 실패: {e}")


def get_hashkey(data: dict):
    """
    주문 API 호출 시 필요한 hashkey 생성
    
    Args:
        data: 주문 요청 바디
    
    Returns:
        str: hashkey
    """
    url = f"{KIS_BASE_URL}/uapi/hashkey"
    headers = {
        "content-type": "application/json",
        "appkey": KIS_APPKEY,
        "appsecret": KIS_APPSECRET
    }
    
    try:
        response = httpx.post(url, headers=headers, json=data, timeout=10.0)
        response.raise_for_status()
        return response.json()["HASH"]
    except Exception as e:
        raise Exception(f"Hashkey 생성 실패: {e}")


def get_api_headers(tr_id: str, is_order=False, hashkey=None):
    """
    API 호출용 헤더 생성
    
    Args:
        tr_id: 거래ID (예: FHKST01010100)
        is_order: 주문 API 여부
        hashkey: 주문 시 필요한 hashkey
    
    Returns:
        dict: API 요청 헤더
    """
    token = get_access_token()
    
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": KIS_APPKEY,
        "appsecret": KIS_APPSECRET,
        "tr_id": tr_id,
        "custtype": "P"  # 개인
    }
    
    if is_order and hashkey:
        headers["hashkey"] = hashkey
    
    return headers


def get_account_info():
    """
    현재 설정된 계좌 정보 반환
    
    Returns:
        dict: {"account_no": "12345678", "product_code": "01"}
    """
    return {
        "account_no": KIS_ACCOUNT_NO,
        "product_code": KIS_ACCOUNT_PROD
    }


# 초기화: 토큰 미리 발급
if __name__ == "__main__":
    print("KIS API 인증 테스트")
    print(f"Base URL: {KIS_BASE_URL}")
    print(f"App Key: {KIS_APPKEY[:10]}...")
    
    try:
        token = get_access_token()
        print(f"[OK] 토큰 발급 성공: {token[:20]}...")
        
        account = get_account_info()
        print(f"[OK] 계좌: {account['account_no']}-{account['product_code']}")
    except Exception as e:
        print(f"[ERROR] 오류: {e}")

# Force Reload Trigger
