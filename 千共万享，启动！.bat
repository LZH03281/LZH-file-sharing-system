@echo off
setlocal EnableExtensions

set "PROJECT_ROOT=%~dp0"
set "CLIENT_DIR=%PROJECT_ROOT%client"

if exist "%PROJECT_ROOT%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"
    set "PYTHON_ARGS="
) else if exist "%CLIENT_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%CLIENT_DIR%\.venv\Scripts\python.exe"
    set "PYTHON_ARGS="
) else if exist "%PROJECT_ROOT%..\LZH-file-sharing-system-main_03\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%..\LZH-file-sharing-system-main_03\.venv\Scripts\python.exe"
    set "PYTHON_ARGS="
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_EXE=py"
        set "PYTHON_ARGS=-3"
    ) else (
        where python >nul 2>nul
        if errorlevel 1 (
            echo Python was not found. Install Python or create a .venv in the project.
            pause
            exit /b 1
        )
        set "PYTHON_EXE=python"
        set "PYTHON_ARGS="
    )
)

"%PYTHON_EXE%" %PYTHON_ARGS% -c "import PyQt6, requests, websocket" >nul 2>nul
if errorlevel 1 (
    echo Client dependencies are incomplete in the selected Python environment.
    echo Run: "%PYTHON_EXE%" %PYTHON_ARGS% -m pip install -r "%CLIENT_DIR%\requirements.txt"
    pause
    exit /b 1
)

pushd "%CLIENT_DIR%"
"%PYTHON_EXE%" %PYTHON_ARGS% main.py
set "EXIT_CODE=%ERRORLEVEL%"
popd

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Client exited with code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%