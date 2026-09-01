@echo off
chcp 65001 >NUL
setlocal
set "LORA=F:\fluxGenerationForLora\stable-diffusion-webui-forge\models\Lora"
set "BAK=%LORA%\_sdxl_disabled"
if not exist "%BAK%" mkdir "%BAK%"
echo Moving SDXL LoRA copies that break Flux (alias collision)...
for %%f in (Low_Poly_Papercraft.safetensors ningraphix.safetensors) do (
  if exist "%LORA%\%%f" (
    move /Y "%LORA%\%%f" "%BAK%\%%f" >NUL
    echo   moved %%f
  )
)
echo.
echo Flux LoRA should remain:
echo   low-poly-papercraft.safetensors
echo   ningraphix-000031.safetensors
echo.
echo Restart Forge after moving files.
pause
