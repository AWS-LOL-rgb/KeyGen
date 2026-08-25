@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\.."

echo === KEYGEN build ===
where python >nul 2>&1 || (echo Python not found. && exit /b 1)
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python -m pip install pillow -q

echo --- application icon ---
python tools\make_icon.py
if errorlevel 1 (
  echo ERROR: could not write packaging\app.ico
  exit /b 1
)

echo --- PyInstaller onedir ---
if exist dist\KEYGEN rmdir /s /q dist\KEYGEN
python -m PyInstaller --noconfirm --clean packaging\keygen.spec
if errorlevel 1 exit /b 1
if not exist dist\KEYGEN\KEYGEN.exe (
  echo KEYGEN.exe was not produced.
  exit /b 1
)
echo Portable app ready: dist\KEYGEN\KEYGEN.exe

echo --- Inno Setup installer ---
set "ISCC="
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 5\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 5\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC (
  where ISCC.exe >nul 2>&1 && for /f "delims=" %%I in ('where ISCC.exe') do set "ISCC=%%I"
)

if not defined ISCC (
  echo.
  echo ERROR: Inno Setup compiler ISCC.exe was not found.
  echo Install Inno Setup 6 from https://jrsoftware.org/isinfo.php
  echo Then run this script again to get dist\keygen-setup.exe
  echo Portable app is still at dist\KEYGEN\KEYGEN.exe
  exit /b 2
)

echo Compiling with: %ISCC%
if exist dist\keygen-setup.exe del /f /q dist\keygen-setup.exe
"%ISCC%" "%cd%\packaging\keygen.iss"
if errorlevel 1 (
  echo ERROR: Inno Setup compile failed.
  exit /b 1
)
if not exist dist\keygen-setup.exe (
  echo ERROR: ISCC reported success but dist\keygen-setup.exe is missing.
  exit /b 1
)
echo.
echo SUCCESS: dist\keygen-setup.exe

echo --- optional local signature ---
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0make-dev-cert.ps1"
if exist packaging\keygen-dev.pfx (
  set "SIGN_PFX=%cd%\packaging\keygen-dev.pfx"
  set "SIGN_PASSWORD=keygen-dev-local"
  call "%~dp0sign.bat"
  if errorlevel 1 echo Signing skipped or failed — setup.exe is still valid.
)

echo.
echo Built:
echo   dist\KEYGEN\KEYGEN.exe     application
echo   dist\keygen-setup.exe      installer
endlocal
