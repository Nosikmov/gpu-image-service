@echo off
chcp 65001 >NUL
setlocal
cd /d "%~dp0"

REM Download LoRA checkpoints from old GPU server into loras/ for git LFS push.
set "REMOTE=ubuntu@dada"
set "REMOTE_DIR=gpu-image-service/train-a5000/output/gf_lowpoly_v2"
set "LOCAL=loras\gf_lowpoly_v2"

if "%REMOTE%"=="ubuntu@YOUR_OLD_SERVER" (
  echo Edit REMOTE in FETCH_LORAS.bat ^(e.g. ubuntu@1.2.3.4^)
  pause
  exit /b 1
)

if not exist "%LOCAL%" mkdir "%LOCAL%"

echo Fetching from %REMOTE%:%REMOTE_DIR%/
scp "%REMOTE%:%REMOTE_DIR%/*.safetensors" "%LOCAL%\"
if errorlevel 1 (
  echo scp failed
  pause
  exit /b 1
)

echo.
echo OK. Files in %LOCAL%:
dir /b "%LOCAL%\*.safetensors"
echo.
echo Next ^(Git Bash or WSL^):
echo   git lfs install
echo   git add loras/
echo   git commit -m "Add gf_lowpoly_v2 LoRA weights"
echo   git push
pause
