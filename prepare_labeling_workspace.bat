@echo off
rem ============================================================
rem  prepare_labeling_workspace.bat  - one-stop labeling tool
rem
rem  Double-click, enter ONE image folder path, and it will:
rem    1. arrange a standard YOLO workspace around the images
rem       (images\ labels\ data.yaml):
rem         - folder named "images"      -> workspace = its parent
rem         - folder containing images\  -> workspace = the folder
rem         - folder with loose pictures -> pictures are moved
rem                                         into a new images\
rem    2. auto-label every image with the best labeler weight
rem       (trained on all 593 = 500 generated + 93 real photos):
rem         runs\detect\mix593_all\yolo26s\weights\best.pt
rem       labels go to labels\ ; a root data.yaml is created when
rem       missing (never overwritten - GUI-added classes are safe)
rem
rem  Existing label files are skipped (never re-labeled).
rem  Behavior spec: D:\yolo\COMMANDS.md section "打标一键工具"
rem ============================================================
setlocal

set "PY=D:\yolo\.venv\Scripts\python.exe"
set "AUTOLABEL=D:\yolo\autolabel.py"
set "MODEL=D:\yolo\runs\detect\mix593_all\yolo26s\weights\best.pt"
set "CONF=0.25"

if not exist "%PY%" goto err_nopy
if not exist "%AUTOLABEL%" goto err_noscript
if not exist "%MODEL%" goto err_nomodel

set /p "SRC=Please enter the image folder path: "
if not defined SRC goto err_empty
set SRC=%SRC:"=%
if not defined SRC goto err_empty
rem strip one trailing backslash unless it is a drive root like D:\
if not "%SRC:~-1%"=="\" goto src_ok
if "%SRC:~-2%"==":\" goto src_ok
set SRC=%SRC:~0,-1%
:src_ok
if not exist "%SRC%\" goto err_notdir

rem ---- step 1: arrange workspace layout ----
for %%I in ("%SRC%") do (
    set "BASENAME=%%~nxI"
    set "PARENT=%%~dpI"
)
set "WS=%SRC%"
if /i "%BASENAME%"=="images" set "WS=%PARENT%"
rem strip one trailing backslash unless it is a drive root like D:\
if "%WS:~-1%"=="\" if not "%WS:~-2%"==":\" set "WS=%WS:~0,-1%"

set "IMGDIR=%WS%\images"
if exist "%IMGDIR%\" goto have_imgdir
mkdir "%IMGDIR%"
for %%E in (png jpg jpeg webp bmp tif tiff) do (
    if exist "%WS%\*.%%E" move "%WS%\*.%%E" "%IMGDIR%\" >nul
)
echo [OK] loose images moved into "%IMGDIR%"
:have_imgdir

set "LABDIR=%WS%\labels"
if not exist "%LABDIR%\" mkdir "%LABDIR%"

if exist "%WS%\data.yaml" goto have_yaml
>"%WS%\data.yaml" (
echo path: .
echo train: images
echo val: images
echo nc: 1
echo names:
echo   0: Placement Issues
)
echo [OK] data.yaml created: "%WS%\data.yaml"
:have_yaml

rem ---- step 2: auto-label with the best mix593 labeler weight ----
echo.
echo [..] auto-labeling "%IMGDIR%"
echo      model: %MODEL%  conf=%CONF%
echo.
"%PY%" "%AUTOLABEL%" --source "%IMGDIR%" --labels-out "%LABDIR%" --model "%MODEL%" --conf %CONF%
if errorlevel 1 goto err_autolabel

echo.
echo [DONE] workspace ready: %WS%
echo   images\    = %IMGDIR%
echo   labels\    = %LABDIR%  (pre-labeled - please review before training)
echo   data.yaml  = %WS%\data.yaml
echo.
echo Next: review/fix boxes in the annotator GUI:
echo   run D:\yolo\annotator\start_annotator.bat and load "%WS%"
echo.
echo Tips: to re-label from scratch, delete labels\*.txt and run this script
echo again (or run autolabel.py with --overwrite); to tune confidence / switch
echo model: re-run autolabel.py with --conf / --model (script: D:\yolo\autolabel.py).
pause
exit /b 0

:err_nopy
echo.
echo [ERROR] python not found: "%PY%"
pause
exit /b 1

:err_noscript
echo.
echo [ERROR] autolabel script not found: "%AUTOLABEL%"
pause
exit /b 1

:err_nomodel
echo.
echo [ERROR] best weight not found: "%MODEL%"
echo         Train the mix593_all yolo26s model first (see D:\yolo\PROGRESS.md).
pause
exit /b 1

:err_empty
echo.
echo [ERROR] empty path. Enter a folder path like D:\batches\batch001
pause
exit /b 1

:err_notdir
echo.
echo [ERROR] path not found or not a directory: "%SRC%"
pause
exit /b 1

:err_autolabel
echo.
echo [ERROR] auto-labeling failed (see messages above).
echo         The workspace folders/data.yaml are already in place: %WS%
echo         Common causes: no images in the folder, or GPU/env problem.
echo         You can retry manually:
echo           "%PY%" "%AUTOLABEL%" --source "%IMGDIR%" --labels-out "%LABDIR%"
pause
exit /b 1
