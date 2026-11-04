@echo off
cd /d "%~dp0"
java -version >nul 2>&1
if errorlevel 1 (
 echo Install Java 11 or later and reopen this window.
 pause
 exit /b 1
)
python server.py
pause
