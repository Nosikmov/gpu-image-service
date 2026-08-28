@echo off
chcp 65001 >NUL
cd /d "%~dp0"

set "FORGE_DIR=F:\fluxGenerationForLora\stable-diffusion-webui-forge"
set "FORGE_URL=http://127.0.0.1:7860"
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"
set "CURL=curl.exe"

echo === gameFarmling LoRA curation ===
echo Forge:  %FORGE_URL%
echo Review: http://127.0.0.1:8765/
echo.

REM Free port 8765 if old reviewer is stuck
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8765" ^| findstr LISTENING') do (
  echo Stopping old process on 8765 PID %%p
  taskkill /PID %%p /F >NUL 2>&1
)

echo Checking Forge API...
%CURL% -sf --connect-timeout 3 --max-time 5 "%FORGE_URL%/sdapi/v1/sd-models" >NUL 2>&1
if errorlevel 1 goto start_forge
echo [1/2] Forge already up
goto forge_ok

:start_forge
echo [1/2] Forge not ready - starting webui-user.bat ...
start "Forge WebUI" /D "%FORGE_DIR%" cmd /c webui-user.bat
echo Waiting for Forge API up to 10 min. Do not close this window.
set /a _n=0

:wait_forge
timeout /t 5 /nobreak >NUL
%CURL% -sf --connect-timeout 3 --max-time 5 "%FORGE_URL%/sdapi/v1/sd-models" >NUL 2>&1
if not errorlevel 1 goto forge_ok
set /a _n+=1
echo   still waiting... %_n%/120
if %_n% GEQ 120 goto forge_fail
goto wait_forge

:forge_fail
echo Forge did not start. Run webui-user.bat manually, then this file again.
pause
exit /b 1

:forge_ok
echo Forge OK
set "FORGE_DIR=%FORGE_DIR%"
echo [2/2] Starting auto-loop: review + reject redo + new prompts
echo Keep this window open. Browser: http://127.0.0.1:8765/
echo.
python lora-curation\auto_loop.py --port 8765 --forge %FORGE_URL%
echo.
echo Auto-loop exited.
pause
