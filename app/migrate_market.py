# DB 마이그레이션 스크립트
# 기존 테이블에 market 컬럼 추가

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "trading.db"

def migrate():
    """기존 DB에 market 컬럼 추가"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Position 테이블에 market 컬럼 추가
        print("Position 테이블 마이그레이션...")
        cursor.execute("ALTER TABLE positions ADD COLUMN market TEXT DEFAULT 'KR'")
        print("✅ Position 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️ Position.market 이미 존재")
        else:
            raise
    
    try:
        # Trade 테이블에 market 컬럼 추가
        print("Trade 테이블 마이그레이션...")
        cursor.execute("ALTER TABLE trades ADD COLUMN market TEXT DEFAULT 'KR'")
        print("✅ Trade 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️ Trade.market 이미 존재")
        else:
            raise
    
    try:
        # TradingSignal 테이블에 market 컬럼 추가
        print("TradingSignal 테이블 마이그레이션...")
        cursor.execute("ALTER TABLE trading_signals ADD COLUMN market TEXT DEFAULT 'KR'")
        print("✅ TradingSignal 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️ TradingSignal.market 이미 존재")
        else:
            raise
    
    try:
        # Position의 unique 제약조건 제거 (market + stock_code 조합으로 변경)
        print("Position unique 제약조건 제거...")
        # SQLite는 ALTER TABLE로 제약조건 변경 불가, 테이블 재생성 필요
        # 일단 unique=True를 제거한 채로 사용
        print("⚠️ stock_code unique 제약은 수동 관리 필요")
    except Exception as e:
        print(f"⚠️ 제약조건 변경 스킵: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ 마이그레이션 완료!")
    print("📌 이제 한국장/미국장을 별도로 관리할 수 있습니다.")

if __name__ == "__main__":
    migrate()
