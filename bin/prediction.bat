@echo off
REM Set UTF-8 code page for proper character encoding
chcp 65001 >nul

REM Force Python to use UTF-8 encoding
set PYTHONIOENCODING=utf-8

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
REM Go up one level to the project root
set PROJECT_ROOT=%SCRIPT_DIR%..
cd /d "%PROJECT_ROOT%"

REM Check if virtual environment is already activated
if "%VIRTUAL_ENV%"=="" (
    echo Activating virtual environment...
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
    ) else (
        echo ERROR: Virtual environment not found at venv\Scripts\activate.bat
        exit /b 1
    )
) else (
    echo Virtual environment already activated: %VIRTUAL_ENV%
)

REM Set Python path from venv
set PYTHON_EXE=%PROJECT_ROOT%\venv\Scripts\python.exe

powershell -Command "& '%PYTHON_EXE%' app/cli.py --league premier_league --command predict | Out-File -FilePath premier_league.txt -Encoding UTF8"
powershell -Command "& '%PYTHON_EXE%' app/cli.py --league bundesliga_1 --command predict | Out-File -FilePath budesliga.txt -Encoding UTF8"
powershell -Command "& '%PYTHON_EXE%' app/cli.py --league laliga_1 --command predict | Out-File -FilePath laliga.txt -Encoding UTF8"
powershell -Command "& '%PYTHON_EXE%' app/cli.py --league le_championnat --command predict | Out-File -FilePath le_championnat.txt -Encoding UTF8"
powershell -Command "& '%PYTHON_EXE%' app/cli.py --league serie_a --command predict | Out-File -FilePath serie_a.txt -Encoding UTF8"

