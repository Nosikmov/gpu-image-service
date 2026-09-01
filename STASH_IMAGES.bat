@echo off
chcp 65001 >NUL
cd /d "%~dp0"
echo === Archive curation images (fresh generation) ===
python lora-curation\stash_images.py %*
echo.
pause
