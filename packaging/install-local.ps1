# Install KEYGEN for the current user (no Inno Setup required).
# Copies dist\KEYGEN -> %LOCALAPPDATA%\KEYGEN and optional desktop shortcut.

param(
    [switch]$DesktopShortcut = $true
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$src = Join-Path $root "dist\KEYGEN"
$dst = Join-Path $env:LOCALAPPDATA "KEYGEN"

if (-not (Test-Path (Join-Path $src "KEYGEN.exe"))) {
    Write-Error "Build first: packaging\build.bat   (missing dist\KEYGEN\KEYGEN.exe)"
}

if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
New-Item -ItemType Directory -Path $dst | Out-Null
Copy-Item -Path (Join-Path $src "*") -Destination $dst -Recurse -Force

$exe = Join-Path $dst "KEYGEN.exe"
$wsh = New-Object -ComObject WScript.Shell
$startDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
if (-not (Test-Path $startDir)) { New-Item -ItemType Directory -Path $startDir | Out-Null }
$lnk = $wsh.CreateShortcut((Join-Path $startDir "KEYGEN.lnk"))
$lnk.TargetPath = $exe
$lnk.WorkingDirectory = $dst
$lnk.IconLocation = $exe
$lnk.Save()

if ($DesktopShortcut) {
    $desk = [Environment]::GetFolderPath("Desktop")
    $dlnk = $wsh.CreateShortcut((Join-Path $desk "KEYGEN.lnk"))
    $dlnk.TargetPath = $exe
    $dlnk.WorkingDirectory = $dst
    $dlnk.IconLocation = $exe
    $dlnk.Save()
}

Write-Host "Installed to $dst"
Write-Host "Launching..."
Start-Process $exe
