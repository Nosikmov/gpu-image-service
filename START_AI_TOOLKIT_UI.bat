@echo off
chcp 65001 >NUL
setlocal EnableExtensions

set "TOOLKIT=F:\fluxGenerationForLora\ai-toolkit"
set "TEMP=F:\atk-tmp"
set "TMP=F:\atk-tmp"
if not exist "%TEMP%" mkdir "%TEMP%"

if not exist "%TOOLKIT%\.venv\Scripts\python.exe" (
  echo Toolkit not installed. Run SETUP_AI_TOOLKIT.bat first.
  pause
  exit /b 1
)

echo Starting Ostris AI-Toolkit UI at http://localhost:8675
cd /d "%TOOLKIT%"
python -m manager launch
pause
