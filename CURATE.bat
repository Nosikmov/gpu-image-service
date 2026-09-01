@echo off
chcp 65001 >NUL
cd /d "%~dp0"

set "FORGE_DIR=F:\fluxGenerationForLora\stable-diffusion-webui-forge"
set "FORGE_URL=http://127.0.0.1:7860"
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"
set "CURL=curl.exe"

echo === gf_lowpoly curation (4070) ===
echo Forge:  %FORGE_URL%
echo Review: http://127.0.0.1:8765/
echo.

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8765" ^| findstr LISTENING') do (
  taskkill /PID %%p /F >NUL 2>&1
)

%CURL% -sf --connect-timeout 3 "%FORGE_URL%/sdapi/v1/sd-models" >NUL 2>&1
if errorlevel 1 (
  echo Starting Forge...
  start "Forge" /D "%FORGE_DIR%" cmd /c webui-user.bat
  set /a _n=0
  :wait_forge
  timeout /t 5 /nobreak >NUL
  %CURL% -sf --connect-timeout 3 "%FORGE_URL%/sdapi/v1/sd-models" >NUL 2>&1
  if not errorlevel 1 goto forge_ok
  set /a _n+=1
  if %_n% GEQ 120 exit /b 1
  goto wait_forge
)
:forge_ok
set "FORGE_DIR=%FORGE_DIR%"
python lora-curation\auto_loop.py --port 8765 --forge %FORGE_URL%
pause
