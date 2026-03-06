@echo off
echo ============================================
echo  FANUC Predictive Maintenance - Quick Start
echo ============================================
echo.

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Check for Node
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH.
    pause
    exit /b 1
)

:: Install backend deps
echo [1/4] Installing Python dependencies...
cd /d "%~dp0backend"
pip install -r requirements.txt --quiet

:: Start backend
echo [2/4] Starting Flask backend...
start "Flask Backend" cmd /c "python app.py"
timeout /t 5 /nobreak >nul

:: Install frontend deps
echo [3/4] Installing React dependencies (first time may take a minute)...
cd /d "%~dp0frontend"
call npm install --silent

:: Start frontend
echo [4/4] Starting React frontend...
start "React Frontend" cmd /c "npm start"

echo.
echo ============================================
echo  Backend:  http://localhost:5000
echo  Frontend: http://localhost:3000
echo ============================================
echo.
echo Both servers are starting. The browser will open automatically.
pause
