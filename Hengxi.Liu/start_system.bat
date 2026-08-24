@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo =====================================
echo MPM Knowledge Graph System Starting
echo =====================================
echo.
echo [Security] Neo4j configuration
set /p "NEO4J_PASSWORD=Enter Neo4j password: "
echo.
set /p "MPM_API_KEY=Enter local API key: "
echo.

if "%NEO4J_PASSWORD%"=="" (
    echo [ERROR] Neo4j password cannot be empty.
    pause
    exit /b 1
)
if "%MPM_API_KEY%"=="" (
    echo [ERROR] Local API key cannot be empty.
    pause
    exit /b 1
)

set "NEO4J_URI=bolt://127.0.0.1:7687"
set "NEO4J_USERNAME=neo4j"
set "MPM_API_BASE_URL=http://127.0.0.1:8000"

if not exist "main.py" (
    echo [ERROR] main.py not found.
    pause
    exit /b 1
)
if not exist "app.py" (
    echo [ERROR] app.py not found.
    pause
    exit /b 1

echo Starting Backend...
start "MPM Backend - FastAPI" cmd /k "set NEO4J_URI=%NEO4J_URI%&& set NEO4J_USERNAME=%NEO4J_USERNAME%&& set NEO4J_PASSWORD=%NEO4J_PASSWORD%&& set MPM_API_KEY=%MPM_API_KEY%&& python -m uvicorn main:app --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

echo Starting Frontend...
start "MPM Frontend - Streamlit" cmd /k "set MPM_API_BASE_URL=%MPM_API_BASE_URL%&& set MPM_API_KEY=%MPM_API_KEY%&& python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501"

echo.
echo =====================================
echo System Started
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:8501
echo Neo4j:    bolt://127.0.0.1:7687
echo =====================================
echo.
echo Local API key authentication is ENABLED.
echo All backend API requests require X-API-Key.
echo Invalid or missing keys are rejected with HTTP 401.
echo Query input is validated and Cypher parameters are used.
echo Close the Backend and Frontend windows to stop the system.
echo.
pause
endlocal
