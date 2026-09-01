@echo off
chcp 65001 >NUL
cd /d "%~dp0"
python lora-curation\stash_images.py %*
pause
