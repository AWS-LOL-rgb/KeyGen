@echo off
REM Sign KEYGEN.exe and keygen-setup.exe with Authenticode.
REM Requires: Windows SDK signtool + a purchased code-signing certificate.
REM Self-signed certificates do NOT clear SmartScreen.
REM
REM Set these before running, or edit below:
REM   SIGN_PFX      path to .pfx
REM   SIGN_PASSWORD pfx password
REM   SIGN_TS       timestamp URL (default DigiCert)

setlocal
cd /d "%~dp0\.."

if not defined SIGN_PFX (
  echo Set SIGN_PFX to your .pfx file. A commercial Authenticode cert is required.
  echo Self-signed will not stop SmartScreen.
  exit /b 1
)
if not defined SIGN_TS set "SIGN_TS=http://timestamp.digicert.com"

set "SIGNTOOL="
for %%P in (
  "%ProgramFiles(x86)%\Windows Kits\10\bin\x64\signtool.exe"
  "%ProgramFiles(x86)%\Windows Kits\10\App Certification Kit\signtool.exe"
) do if exist %%P set "SIGNTOOL=%%~P"
if not defined SIGNTOOL (
  where signtool >nul 2>&1 && set "SIGNTOOL=signtool"
)
if not defined SIGNTOOL (
  echo signtool.exe not found. Install Windows SDK.
  exit /b 1
)

set TARGETS=
if exist dist\KEYGEN\KEYGEN.exe set TARGETS=%TARGETS% "dist\KEYGEN\KEYGEN.exe"
if exist dist\keygen-setup.exe set TARGETS=%TARGETS% "dist\keygen-setup.exe"
if "%TARGETS%"=="" (
  echo Nothing to sign. Build first: packaging\build.bat
  exit /b 1
)

"%SIGNTOOL%" sign /fd SHA256 /td SHA256 /tr "%SIGN_TS%" /f "%SIGN_PFX%" /p "%SIGN_PASSWORD%" %TARGETS%
if errorlevel 1 exit /b 1
"%SIGNTOOL%" verify /pa %TARGETS%
echo Signed.
endlocal
