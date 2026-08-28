@echo off
chcp 65001 >NUL
setlocal EnableExtensions
cd /d "%~dp0"

set "TOOLKIT=F:\fluxGenerationForLora\ai-toolkit"
set "TEMP=F:\atk-tmp"
set "TMP=F:\atk-tmp"
set "UV_CACHE_DIR=%TOOLKIT%\.cache\uv"
set "PIP_CACHE_DIR=%TOOLKIT%\.cache\pip"
if not exist "%TEMP%" mkdir "%TEMP%"
if not exist "%UV_CACHE_DIR%" mkdir "%UV_CACHE_DIR%"

echo === Ostris AI-Toolkit setup ===
echo Folder: %TOOLKIT%
echo.

if not exist "%TOOLKIT%\run.py" (
  echo Cloning ostris/ai-toolkit ...
  git clone --depth 1 https://github.com/ostris/ai-toolkit.git "%TOOLKIT%"
  if errorlevel 1 (
    echo Clone failed.
    pause
    exit /b 1
  )
)

git config --global core.longpaths true >NUL 2>&1

cd /d "%TOOLKIT%"
where python >NUL 2>&1
if errorlevel 1 (
  echo ERROR: python not on PATH
  pause
  exit /b 1
)

echo Installing / syncing environment ^(manager, CUDA torch, deps^)...
echo First run can take several minutes.
echo.
python -m manager sync --force
if errorlevel 1 (
  echo.
  echo Sync failed. Retry this bat, or open run_windows.bat inside ai-toolkit.
  pause
  exit /b 1
)

copy /Y "%~dp0lora-curation\train\gf_lowpoly_flux_4070.yaml" "%TOOLKIT%\config\gf_lowpoly_flux_4070.yaml" >NUL

echo.
echo OK. Next:
echo   TRAIN_LORA.bat          - train gf_lowpoly
echo   START_AI_TOOLKIT_UI.bat - web UI http://localhost:8675
echo.
pause
