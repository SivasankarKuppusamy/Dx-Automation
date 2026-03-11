@echo off
REM Batch file to start Salesforce Automation UI Server
REM This will start the Flask server and open the UI in your default browser

echo ========================================
echo  Salesforce Automation UI Launcher
echo ========================================
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

echo [1/2] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.7 or higher from https://www.python.org/
    pause
    exit /b 1
)
echo Python found!
echo.

echo ========================================
echo  Server is starting on http://localhost:5000
echo  Opening browser in 3 seconds...
echo  Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start Flask server in the background
start /B python app.py

REM Wait 3 seconds for server to start
timeout /t 3 /nobreak >nul

REM Open default browser
start http://localhost:5000

REM Keep the window open to show server logs
echo.
echo Server is running. Close this window to stop the server.
echo Or press Ctrl+C to stop the server.
echo.
pause
