@echo off
chcp 65001 >NUL
setlocal
cd /d "%~dp0"

REM Pull latest LoRA from 4090 server -> local Forge models\Lora\
REM Edit REMOTE and TRAIN_NAME if needed.

set "REMOTE=ubuntu@dada"
set "TRAIN_NAME=gf_lowpoly_v2"
set "FORGE=%~dp0..\stable-diffusion-webui-forge"
set "LORA_NAME=gf_lowpoly.safetensors"

set "REMOTE_DIR=gpu-image-service/train-a5000/output/%TRAIN_NAME%"
set "DST=%FORGE%\models\Lora\%LORA_NAME%"

echo Remote: %REMOTE%:%REMOTE_DIR%
echo Local:  %DST%
echo.

scp "%REMOTE%:%REMOTE_DIR%/%TRAIN_NAME%.safetensors" "%DST%.download"
if errorlevel 1 (
  echo Trying latest numbered checkpoint...
  for /f "delims=" %%F in ('ssh %REMOTE% "ls -1 %REMOTE_DIR%/%TRAIN_NAME%_*.safetensors 2^/dev/null | tail -1"') do set "REMOTE_FILE=%%F"
  if not defined REMOTE_FILE (
    echo scp failed
    pause
    exit /b 1
  )
  scp "%REMOTE%:!REMOTE_FILE!" "%DST%.download"
)

move /Y "%DST%.download" "%DST%"
echo.
echo OK: %DST%
echo Open Forge on 4070, model flux1-dev-fp8, Automatic fp16 LoRA
echo Prompt: ^<lora:lowpoly_flux:0.9^> ^<lora:gf_lowpoly:1.0^>, gf_lowpoly, ps1 game screenshot, ...
pause
