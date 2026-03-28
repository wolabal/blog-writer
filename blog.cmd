@echo off
set "PROJECT_ROOT=D:\workspace\blog-writer"
set "PYTHON=%PROJECT_ROOT%\venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo [ERROR] Missing project virtualenv Python: %PYTHON%
    echo Create the venv and install requirements first.
    exit /b 1
)
"%PYTHON%" "%PROJECT_ROOT%\blog_runtime.py" %*
