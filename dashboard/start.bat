@echo off
chcp 65001 > nul
title The 4th Path - Control Panel

echo ================================================
echo   The 4th Path · Control Panel
echo ================================================

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

:: Python 가상환경 활성화
if exist "%PROJECT_ROOT%\venv\Scripts\activate.bat" (
    echo [*] 가상환경 활성화...
    call "%PROJECT_ROOT%\venv\Scripts\activate.bat"
) else if exist "%PROJECT_ROOT%\.venv\Scripts\activate.bat" (
    call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
)

:: 백엔드 의존성 확인
echo [*] FastAPI 의존성 확인...
pip install fastapi uvicorn python-dotenv --quiet 2>nul

:: 프론트엔드 의존성 설치
if not exist "%SCRIPT_DIR%frontend\node_modules" (
    echo [*] npm 패키지 설치 중...
    cd /d "%SCRIPT_DIR%frontend"
    npm install
)

:: 프론트엔드 빌드
echo [*] 프론트엔드 빌드 중...
cd /d "%SCRIPT_DIR%frontend"
npm run build

if errorlevel 1 (
    echo [!] 프론트엔드 빌드 실패!
    pause
    exit /b 1
)

:: 백엔드 서버 시작
echo [*] 대시보드 서버 시작...
echo.
echo   접속 주소: http://localhost:8080
echo   종료하려면 이 창을 닫으세요.
echo.

cd /d "%PROJECT_ROOT%"
python -m uvicorn dashboard.backend.server:app --host 0.0.0.0 --port 8080

pause
