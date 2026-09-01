@echo off
chcp 65001 >NUL
cd /d "%~dp0"
python rebuild_captions.py
pause
