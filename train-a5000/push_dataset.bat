@echo off
chcp 65001 >NUL
cd /d "%~dp0"

REM --- set your server ---
set "REMOTE=root@YOUR_SERVER_IP"
set "DEST=/root/gpu-image-service/train-a5000/dataset"

if "%REMOTE%"=="root@YOUR_SERVER_IP" (
  echo Edit REMOTE in push_dataset.bat first!
  pause
  exit /b 1
)

if not exist "train-a5000\dataset\*.png" (
  echo No dataset. Run EXPORT_FOR_TRAIN.bat first.
  pause
  exit /b 1
)

echo Uploading train-a5000\dataset to %REMOTE%:%DEST%
scp -r train-a5000\dataset\*.png train-a5000\dataset\*.txt "%REMOTE%:%DEST%/"
if errorlevel 1 (
  echo scp failed
  pause
  exit /b 1
)

echo Done. On server: cd ~/gpu-image-service/train-a5000 ^&^& ./bootstrap.sh
pause
