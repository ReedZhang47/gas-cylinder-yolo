@echo off
setlocal
rem stop_server.bat - stop the YOLO annotator server (port 8085 by default).
rem Usage: stop_server.bat [port]

set "PORT=8085"
if not "%~1"=="" set "PORT=%~1"

set "FOUND=0"
for /f "tokens=5" %%p in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%PORT% "') do (
  set "FOUND=1"
  echo [INFO] Stopping service on port %PORT% (PID %%p)
  taskkill /PID %%p /F
)
if "%FOUND%"=="0" (
  echo [INFO] No service is listening on port %PORT%.
  exit /b 0
)

timeout /t 1 /nobreak >nul 2>&1
netstat -ano | findstr "LISTENING" | findstr ":%PORT% " >nul 2>&1
if errorlevel 1 (
  echo [INFO] Port %PORT% is now free.
) else (
  echo [ERROR] Port %PORT% is still in use. Try: taskkill /PID <pid> /F  (list PIDs via: netstat -ano ^| findstr :%PORT%)
)
exit /b 0