@echo off
chcp 65001 >NUL
cd /d "%~dp0"

echo === Export approved images for FLUX LoRA training ===
python lora-curation\export_dataset.py --caption-mode train
if errorlevel 1 goto fail

call train-a5000\sync_dataset.bat
if errorlevel 1 goto fail

for /f %%A in ('dir /b "train-a5000\dataset\*.png" 2^>nul ^| find /c /v ""') do set PNG=%%A
echo.
echo OK: %PNG% images ready in train-a5000\dataset\
echo Next: edit REMOTE in push_dataset.bat and run it, OR git push + sync on server
goto end

:fail
echo Export failed.
pause
exit /b 1

:end
pause
