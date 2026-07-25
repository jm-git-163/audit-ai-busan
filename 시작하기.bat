@echo off
chcp 65001 >nul
cd /d "%~dp0"
title AuditAI Busan — 예산 집행 상담

echo.
echo  ========================================
echo   AuditAI Busan  예산 집행 상담 시스템
echo  ========================================
echo.
echo  로컬 서버(server.py)를 시작합니다.
echo  AI는 .env 의 OPENAI_API_KEY 를 읽습니다.
echo.
echo  주소: http://127.0.0.1:8765/index.html
echo  (HTML 파일을 직접 열면 AI가 안 됩니다)
echo.
echo  종료: 이 창을 닫거나 Ctrl+C
echo.

set PORT=8765
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
    if /i "%%a"=="PORT" set "PORT=%%b"
  )
)

REM 이전에 켜 둔 python -m http.server 가 있으면 AI(/api)가 404 납니다 → 포트 비우기
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT% " ^| findstr LISTENING') do (
  echo  [안내] 포트 %PORT% 사용 중(PID %%p) → 종료 후 server.py 로 재시작
  taskkill /F /PID %%p >nul 2>&1
)
timeout /t 1 /nobreak >nul

where py >nul 2>&1
if %errorlevel%==0 (
  start "" "http://127.0.0.1:%PORT%/index.html"
  py -u server.py
  goto :eof
)

where python >nul 2>&1
if %errorlevel%==0 (
  start "" "http://127.0.0.1:%PORT%/index.html"
  python -u server.py
  goto :eof
)

echo [안내] Python이 없어 index.html을 직접 엽니다.
echo        AI 해설이 필요하면 Python 설치 후 다시 실행하세요.
start "" "%~dp0index.html"
pause
