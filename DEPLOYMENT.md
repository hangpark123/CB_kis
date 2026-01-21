# 사내망 배포 가이드

## 📋 개요
AntTrading Pro를 사내 네트워크에서 다른 PC들이 접속할 수 있도록 배포하는 방법입니다.

---

## 🚀 빠른 시작

### 1. 서버 실행
```cmd
start_server.bat
```

서버가 시작되면 다음과 같이 표시됩니다:
```
[AntTrading Pro] 서버 시작 중...
[INFO] 서버 시작 중... (Ctrl+C로 종료)
[INFO] 사내망 접속 주소: http://[YOUR-PC-IP]:8000
```

### 2. PC IP 주소 확인
**명령 프롬프트(CMD)에서:**
```cmd
ipconfig
```

**IPv4 주소**를 찾으세요 (예: `192.168.1.100`)

### 3. 사내망에서 접속
다른 PC의 브라우저에서:
```
http://192.168.1.100:8000
```
(IP 주소는 위에서 확인한 서버 PC의 IP로 변경)

---

## 🔧 상세 설정

### Windows 방화벽 설정

#### 방법 1: GUI (추천)
1. **Windows 검색** → "고급 보안이 포함된 Windows Defender 방화벽" 실행
2. 왼쪽 메뉴 → **인바운드 규칙** 클릭
3. 오른쪽 메뉴 → **새 규칙...** 클릭
4. 규칙 유형: **포트** 선택 → 다음
5. 프로토콜: **TCP**, 특정 로컬 포트: **8000** 입력 → 다음
6. 작업: **연결 허용** 선택 → 다음
7. 프로필: **도메인**, **개인**, **공용** 모두 체크 → 다음
8. 이름: `AntTrading Pro Server` 입력 → 마침

#### 방법 2: PowerShell (관리자 권한)
```powershell
New-NetFirewallRule -DisplayName "AntTrading Pro Server" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

---

## 📊 서버 상태 확인

### 로컬에서 테스트
```
http://localhost:8000
```

### Health Check API
```
http://localhost:8000/api/health
```
응답: `{"ok": true}`

---

## 🔄 자동 시작 설정 (선택사항)

Windows 부팅 시 자동으로 서버를 시작하려면:

### 방법 1: 작업 스케줄러
1. **Windows 검색** → "작업 스케줄러" 실행
2. **기본 작업 만들기** 클릭
3. 이름: `AntTrading Server`
4. 트리거: **컴퓨터 시작 시**
5. 작업: **프로그램 시작**
6. 프로그램/스크립트: `C:\Project\CB_kis\start_server.bat`
7. 시작 위치: `C:\Project\CB_kis`

### 방법 2: NSSM (Non-Sucking Service Manager)
```cmd
# NSSM 다운로드: https://nssm.cc/download
nssm install AntTradingPro "C:\Project\CB_kis\venv\Scripts\python.exe" "C:\Project\CB_kis\run_server.py"
nssm set AntTradingPro AppDirectory "C:\Project\CB_kis"
nssm start AntTradingPro
```

---

## 🛠️ 문제 해결

### 접속이 안될 때
1. **서버 PC에서 로컬 접속 확인**
   ```
   http://localhost:8000
   ```

2. **방화벽 규칙 확인**
   - Windows Defender 방화벽에서 포트 8000이 열려있는지 확인

3. **서버 로그 확인**
   - `start_server.bat` 실행 창에서 에러 메시지 확인

4. **네트워크 연결 확인**
   - 서버 PC와 클라이언트 PC가 같은 네트워크에 있는지 확인
   - `ping [서버-IP]` 명령으로 연결 테스트

### 포트 변경이 필요할 때
`run_server.py` 파일 수정:
```python
port=8000,  # 원하는 포트 번호로 변경
```

---

## 📌 추천 설정

### 고정 IP 설정 (권장)
서버 PC의 IP가 자동으로 변경되지 않도록:
1. **네트워크 설정** → 이더넷/Wi-Fi 속성
2. **IP 할당**: 수동
3. 고정 IP 주소 설정 (예: 192.168.1.100)

### 성능 최적화
- **CPU 코어 수에 맞게 워커 자동 설정됨**
- 메모리: 최소 4GB 권장
- SSD 사용 권장 (DB 읽기/쓰기 성능)

---

## 📞 지원

문제가 발생하면:
1. 서버 로그 확인
2. Windows 이벤트 뷰어 확인
3. 방화벽/백신 프로그램 예외 추가
