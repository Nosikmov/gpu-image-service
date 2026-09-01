@echo off
chcp 65001 >NUL
:: Run as Administrator — expands Windows pagefile on F: so FLUX training does not kill 32GB RAM
net session >NUL 2>&1
if errorlevel 1 (
  echo Need Administrator. Right-click -^> Run as administrator.
  pause
  exit /b 1
)

echo.
echo Current pagefile peaks during FLUX train can exceed 32GB RAM.
echo This sets a large pagefile on F: ^(48-64 GB^) and turns off auto-manage.
echo REBOOT required after this.
echo.
pause

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$cs = Get-CimInstance Win32_ComputerSystem -EnableAllPrivileges;" ^
  "if ($cs.AutomaticManagedPagefile) { $cs | Set-CimInstance -Property @{AutomaticManagedPagefile=$false}; Start-Sleep 1 };" ^
  "Get-CimInstance Win32_PageFileSetting -ErrorAction SilentlyContinue | ForEach-Object { Remove-CimInstance $_ };" ^
  "New-CimInstance -ClassName Win32_PageFileSetting -Property @{Name='F:\pagefile.sys'; InitialSize=49152; MaximumSize=65536} | Out-Null;" ^
  "Get-CimInstance Win32_PageFileSetting | Format-List Name, InitialSize, MaximumSize;" ^
  "Write-Host 'OK. Reboot Windows, then run TRAIN_LORA.bat again.'"

echo.
pause
