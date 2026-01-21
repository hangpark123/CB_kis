@echo off
REM ========================================
REM AntTrading Pro - 사내망 서버 시작 스크립트
REM ========================================

echo [AntTrading Pro] 서버 시작 중...
echo.

REM 가상환경 활성화 (venv 폴더가 있는 경우)
if exist venv\Scripts\activate.bat (
    echo [INFO] 가상환경 활성화...
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    echo [INFO] 가상환경 활성화...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] 가상환경을 찾을 수 없습니다. 시스템 Python 사용...
)

echo.
echo [INFO] 서버 시작 중... (Ctrl+C로 종료)
echo [INFO] 사내망 접속 주소: http://[YOUR-PC-IP]:8000
echo.

REM 서버 실행
python run_server.py

pause
