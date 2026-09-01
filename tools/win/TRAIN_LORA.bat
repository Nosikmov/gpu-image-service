@echo off
chcp 65001 >NUL
setlocal EnableExtensions
cd /d "%~dp0"

set "TOOLKIT=F:\fluxGenerationForLora\ai-toolkit"
set "CONFIG=%~dp0lora-curation\train\gf_lowpoly_flux_4070.yaml"
set "PY=%TOOLKIT%\.venv\Scripts\python.exe"
set "APPROVED=%~dp0lora-curation\export\approved"

REM Keep caches/temp on F: (HF defaults to C:\Users\...\ .cache\huggingface)
set "TEMP=F:\atk-tmp"
set "TMP=F:\atk-tmp"
set "HF_HOME=F:\fluxGenerationForLora\hf-cache"
set "HF_HUB_CACHE=%HF_HOME%\hub"
set "TRANSFORMERS_CACHE=%HF_HOME%\transformers"
set "TORCH_HOME=F:\fluxGenerationForLora\torch-cache"
set "UV_CACHE_DIR=%TOOLKIT%\.cache\uv"
set "PIP_CACHE_DIR=%TOOLKIT%\.cache\pip"
if not exist "%TEMP%" mkdir "%TEMP%"
if not exist "%HF_HUB_CACHE%" mkdir "%HF_HUB_CACHE%"
if not exist "%TORCH_HOME%" mkdir "%TORCH_HOME%"

echo.
echo  === gf_lowpoly Flux LoRA training (Ostris AI-Toolkit) ===
echo  Config : %CONFIG%
echo  Dataset: %APPROVED%
echo  Output : %TOOLKIT%\output\gf_lowpoly
echo.

if not exist "%PY%" (
  echo ERROR: Toolkit venv not found: %PY%
  echo Run SETUP_AI_TOOLKIT.bat first.
  pause
  exit /b 1
)

if not exist "%CONFIG%" (
  echo ERROR: Missing config: %CONFIG%
  pause
  exit /b 1
)

dir /b "%APPROVED%\*.png" >NUL 2>&1
if errorlevel 1 (
  echo ERROR: No PNG in %APPROVED%
  echo Run: lora-curation\train\EXPORT_AND_TRAIN_HINT.bat
  pause
  exit /b 1
)

REM Sync copy used by UI / optional CLI from toolkit folder
copy /Y "%CONFIG%" "%TOOLKIT%\config\gf_lowpoly_flux_4070.yaml" >NUL

echo Checking Hugging Face login (need access to FLUX.1-dev^)...
"%PY%" -c "from huggingface_hub import get_token; t=get_token(); raise SystemExit(0 if t else 1)"
if errorlevel 1 (
  echo.
  echo No Hugging Face token found.
  echo 1^) Accept license: https://huggingface.co/black-forest-labs/FLUX.1-dev
  echo 2^) Create token:  https://huggingface.co/settings/tokens
  echo 3^) Login below ^(paste token when asked^):
  echo.
  "%TOOLKIT%\.venv\Scripts\hf.exe" auth login
  if errorlevel 1 (
    echo Login failed.
    pause
    exit /b 1
  )
)

echo.
echo Close Forge, browsers, Discord — FLUX needs ~32GB+ peak RAM.
echo If Windows kills it: EXPAND_PAGEFILE_F.bat as Admin, reboot, retry.
echo Training ~2-6 hours. Ctrl+C stops; resume picks last checkpoint.
echo.
pause

cd /d "%TOOLKIT%"
"%PY%" run.py "%CONFIG%"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo Training exited with code %RC%
) else (
  echo Done. Checkpoints: %TOOLKIT%\output\gf_lowpoly\
  echo Copy .safetensors to Forge models\Lora\
)
pause
exit /b %RC%
