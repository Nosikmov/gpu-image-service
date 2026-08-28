@echo off
chcp 65001 >NUL
setlocal EnableExtensions
cd /d "%~dp0"

set "FORGE=F:\fluxGenerationForLora\stable-diffusion-webui-forge"
set "PY=%FORGE%\venv\Scripts\python.exe"
set "SD=%FORGE%\models\Stable-diffusion"
set "LORA=%FORGE%\models\Lora"
set "HF_HOME=F:\fluxGenerationForLora\hf-cache"
set "HF_HUB_CACHE=%HF_HOME%\hub"

if not exist "%PY%" (
  echo ERROR: Forge venv not found: %PY%
  pause
  exit /b 1
)

echo.
echo  === Download SDXL models for curation ===
echo  Checkpoint -^> %SD%\sd_xl_base_1.0.safetensors
echo  LoRA slots -^> %LORA%\Low_Poly_Papercraft.safetensors
echo                 %LORA%\ningraphix.safetensors
echo.

"%PY%" "%~dp0lora-curation\scripts\download_sdxl_models.py"
if errorlevel 1 (
  echo.
  echo Download failed. Check internet / Hugging Face login.
  pause
  exit /b 1
)

echo.
echo OK. Restart Forge and use sd_xl_base_1.0.safetensors.
pause
