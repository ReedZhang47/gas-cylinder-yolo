@echo off
setlocal
rem start_annotator.bat - start the YOLO annotator server WITHOUT any console window.
rem Lives in D:\yolo\annotator\ ; venv is expected at <this>\..\.venv
rem The server has no console. To stop it: click "Stop" in the GUI at
rem http://127.0.0.1:8085 , or run stop_server.bat next to this file.

if "%~1"=="--hidden" goto :run
powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -WindowStyle Hidden -FilePath '%~f0' -ArgumentList '--hidden'"
exit /b

:run
set "PYTHON=%~dp0..\.venv\Scripts\pythonw.exe"
set "APP=%~dp0annotator.py"
set "URL=http://127.0.0.1:8085"
set "PORT=8085"
set "LOG=%~dp0server.log"

if not exist "%PYTHON%" (
  echo [ERROR] pythonw.exe not found: %PYTHON%
  exit /b 1
)
if not exist "%APP%" (
  echo [ERROR] annotator.py not found: %APP%
  exit /b 1
)

netstat -ano | findstr "LISTENING" | findstr ":%PORT% " >nul 2>&1
if not errorlevel 1 (
  start "" "%URL%"
  exit /b 0
)

start "YOLO Annotator" /B "%PYTHON%" "%APP%" >"%LOG%" 2>&1
timeout /t 3 /nobreak >nul 2>&1 || ping -n 4 127.0.0.1 >nul
start "" "%URL%"
exit /b 0