@echo off
chcp 65001 >NUL
setlocal
cd /d "%~dp0"

set "SRC=%~dp0..\lora-curation\export\approved"
set "DST=%~dp0dataset"

if not exist "%SRC%" (
  echo Missing %SRC%
  echo Run: python lora-curation\export_dataset.py --caption-mode train
  pause
  exit /b 1
)

if not exist "%DST%" mkdir "%DST%"
echo Syncing dataset...
robocopy "%SRC%" "%DST%" *.png *.txt /MIR /XD _latent_cache _t_e_cache /NFL /NDL /NJH /NJS /nc /ns /np
if exist "%DST%\_latent_cache" rmdir /s /q "%DST%\_latent_cache"
if exist "%DST%\_t_e_cache" rmdir /s /q "%DST%\_t_e_cache"
set "RC=%ERRORLEVEL%"
if %RC% GEQ 8 (
  echo robocopy failed: %RC%
  pause
  exit /b 1
)

for /f %%A in ('dir /b "%DST%\*.png" 2^>nul ^| find /c /v ""') do set PNG=%%A
echo OK: %PNG% PNG in %DST%
pause
