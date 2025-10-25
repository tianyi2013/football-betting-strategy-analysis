@echo off
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


python app/cli.py --league premier_league --command cleanse
python app/cli.py --league bundesliga_1 --command cleanse
python app/cli.py --league laliga_1 --command cleanse
python app/cli.py --league le_championnat --command cleanse
python app/cli.py --league serie_a --command cleanse
