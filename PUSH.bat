@echo off
chcp 65001 >NUL
cd /d "%~dp0"

set "REMOTE=ubuntu@dada"
set "DEST=gpu-image-service/train-a5000/dataset"

if "%REMOTE%"=="ubuntu@YOUR_SERVER" (
  echo Edit REMOTE in PUSH.bat
  pause
  exit /b 1
)

if not exist "train-a5000\dataset\*.png" (
  echo Run EXPORT.bat first
  pause
  exit /b 1
)

scp train-a5000\dataset\*.png train-a5000\dataset\*.txt "%REMOTE%:%DEST%/"
if errorlevel 1 exit /b 1
echo Done. On server: cd train-a5000 ^&^& ./cycle.sh train
pause
