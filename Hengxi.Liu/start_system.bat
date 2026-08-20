@echo off

echo =====================================
echo MPM Knowledge Graph System Starting
echo =====================================


echo Starting Backend...

start "MPM Backend" cmd /k ^
"D:\Desktop\SURF_2026\MPM_KG_QuerySystem\.venv\Scripts\python.exe D:\Desktop\SURF_2026\MPM_KG_QuerySystem\main.py"


timeout /t 5


echo Starting Frontend...

start "MPM Dashboard" cmd /k ^
"D:\Desktop\SURF_2026\MPM_KG_QuerySystem\.venv\Scripts\streamlit.exe run D:\Desktop\SURF_2026\MPM_KG_QuerySystem\app.py"


echo =====================================
echo System Started
echo =====================================

pause