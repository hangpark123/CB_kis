"""
프로덕션 서버 실행 스크립트
사내망(Internal Network)에서 접속 가능하도록 설정
"""
import uvicorn
import multiprocessing

if __name__ == "__main__":
    # CPU 코어 수에 따라 워커 수 자동 설정
    workers = multiprocessing.cpu_count()
    
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",  # 모든 네트워크 인터페이스에서 접속 허용
        port=8000,
        workers=workers,
        log_level="info",
        access_log=True,
        reload=False  # 프로덕션에서는 auto-reload 비활성화
    )
