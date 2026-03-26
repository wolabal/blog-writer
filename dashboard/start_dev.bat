@echo off
chcp 65001 > nul
title The 4th Path - Control Panel (개발 모드)

echo ================================================
echo   The 4th Path · Control Panel (개발 모드)
echo ================================================

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

:: Python 가상환경 활성화
if exist "%PROJECT_ROOT%\venv\Scripts\activate.bat" (
    call "%PROJECT_ROOT%\venv\Scripts\activate.bat"
) else if exist "%PROJECT_ROOT%\.venv\Scripts\activate.bat" (
    call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
)

:: 백엔드 의존성 확인
pip install fastapi uvicorn python-dotenv --quiet 2>nul

:: 프론트엔드 의존성 설치
if not exist "%SCRIPT_DIR%frontend\node_modules" (
    echo [*] npm 패키지 설치 중...
    cd /d "%SCRIPT_DIR%frontend"
    npm install
)

echo [*] 백엔드 시작 중...
start "FastAPI Backend" cmd /k "cd /d %PROJECT_ROOT% && python -m uvicorn dashboard.backend.server:app --host 0.0.0.0 --port 8080 --reload"

echo [*] 프론트엔드 개발 서버 시작 중...
start "Vite Frontend" cmd /k "cd /d %SCRIPT_DIR%frontend && npm run dev"

echo.
echo   백엔드: http://localhost:8080
echo   프론트: http://localhost:5173 (개발 서버)
echo.
echo 두 창이 열렸습니다. 각 창을 닫으면 서버가 종료됩니다.
pause
