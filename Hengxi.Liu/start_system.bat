@echo off
setlocal

cd /d "%~dp0"

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=%PROJECT_DIR%.venv\Scripts\python.exe"
set "STREAMLIT_EXE=%PROJECT_DIR%.venv\Scripts\streamlit.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Virtual environment Python was not found:
    echo %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist "%STREAMLIT_EXE%" (
    echo [ERROR] Streamlit executable was not found:
    echo %STREAMLIT_EXE%
    pause
    exit /b 1
)

if not exist "%PROJECT_DIR%main.py" (
    echo [ERROR] main.py was not found.
    pause
    exit /b 1
)

if not exist "%PROJECT_DIR%app.py" (
    echo [ERROR] app.py was not found.
    pause
    exit /b 1
)

echo =====================================
echo MPM Knowledge Graph System Starting
echo =====================================
echo.

echo [Security] Neo4j configuration
set /p "NEO4J_PASSWORD=Enter Neo4j password: "
if "%NEO4J_PASSWORD%"=="" (
    echo [ERROR] Neo4j password cannot be empty.
    pause
    exit /b 1
)

echo.
set /p "MPM_API_KEY=Enter local API key: "
if "%MPM_API_KEY%"=="" (
    echo [ERROR] API key cannot be empty.
    pause
    exit /b 1
)

set "NEO4J_URI=bolt://127.0.0.1:7687"
set "NEO4J_USERNAME=neo4j"
set "MPM_API_BASE_URL=http://127.0.0.1:8000"


echo.
echo Starting Backend...
start "MPM Backend" cmd /k ""%PYTHON_EXE%" "%PROJECT_DIR%main.py""

timeout /t 5 /nobreak >nul

echo.
echo Starting Frontend...
start "MPM Dashboard" cmd /k ""%STREAMLIT_EXE%" run "%PROJECT_DIR%app.py" --server.address 127.0.0.1 --server.port 8501"

echo.
echo =====================================
echo System Started
 echo Backend:  http://127.0.0.1:8000
 echo Frontend: http://127.0.0.1:8501
 echo Neo4j:    bolt://127.0.0.1:7687
 echo =====================================
echo.
echo API authentication and input validation are enabled.
echo Close the Backend and Dashboard windows to stop the system.

pause
endlocal
