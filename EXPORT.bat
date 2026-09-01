@echo off
chcp 65001 >NUL
cd /d "%~dp0"

echo === Export approved -> train-a5000/dataset ===
python lora-curation\export_dataset.py --caption-mode train
if errorlevel 1 goto fail

set "SRC=%~dp0lora-curation\export\approved"
set "DST=%~dp0train-a5000\dataset"
if not exist "%DST%" mkdir "%DST%"
robocopy "%SRC%" "%DST%" *.png *.txt /MIR /NFL /NDL /NJH /NJS /nc /ns /np
if %ERRORLEVEL% GEQ 8 goto fail

python train-a5000\rebuild_captions.py
if errorlevel 1 goto fail

for /f %%A in ('dir /b "%DST%\*.png" 2^>nul ^| find /c /v ""') do set PNG=%%A
echo OK: %PNG% images in train-a5000\dataset
echo Next: PUSH.bat or git push
goto end

:fail
echo Failed.
pause
exit /b 1
:end
pause
