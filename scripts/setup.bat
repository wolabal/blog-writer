@echo off
echo ========================================
echo  Blog Engine Setup
echo ========================================

REM Create Python venv
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create Python venv. Please install Python 3.11+
    pause
    exit /b 1
)

REM Install packages
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Package installation failed.
    pause
    exit /b 1
)

REM Copy .env file if not exists
if not exist .env (
    copy .env.example .env
    echo [OK] .env file created. Please fill in your API keys: .env
)

REM Create data directories
if not exist data\topics mkdir data\topics
if not exist data\collected mkdir data\collected
if not exist data\discarded mkdir data\discarded
if not exist data\pending_review mkdir data\pending_review
if not exist data\published mkdir data\published
if not exist data\analytics mkdir data\analytics
if not exist data\images mkdir data\images
if not exist data\drafts mkdir data\drafts
if not exist logs mkdir logs

REM Register scheduler.py in Windows Task Scheduler
set SCRIPT_PATH=%~dp0bots\scheduler.py
set PYTHON_PATH=%~dp0venv\Scripts\pythonw.exe

schtasks /query /tn "BlogEngine" >nul 2>&1
if errorlevel 1 (
    schtasks /create /tn "BlogEngine" /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" /sc onlogon /rl highest /f
    echo [OK] BlogEngine registered in Windows Task Scheduler
) else (
    echo [INFO] BlogEngine task already registered.
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Open .env and fill in all API keys
echo 2. Run scripts\get_token.py to get Google OAuth token
echo 3. Update BLOG_MAIN_ID in config\blogs.json with your actual blog ID
echo 4. Start scheduler with: python bots\scheduler.py
echo.
pause
