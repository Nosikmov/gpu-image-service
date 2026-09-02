@echo off
chcp 65001 >NUL
cd /d "%~dp0"
git lfs install
git add loras/
git status
echo.
echo If loras\gf_lowpoly_v2\*.safetensors present:
echo   git commit -m "Add gf_lowpoly_v2 LoRA weights"
echo   git push
pause
