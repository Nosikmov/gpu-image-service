@echo off
chcp 65001 >NUL
cd /d "%~dp0\.."

echo === Export approved dataset ===
python export_dataset.py --caption-mode train
if errorlevel 1 pause & exit /b 1

echo.
echo Dataset: %~dp0..\export\approved
echo Next: double-click TRAIN_LORA.bat in gpu-image-service root
echo       (Ostris AI-Toolkit + gf_lowpoly_flux_4070.yaml)
echo.
pause
