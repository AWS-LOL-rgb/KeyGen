#!/usr/bin/env bash
# Linux helper: compiles sources / tests. Windows installer is build.bat + Inno Setup.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pytest test_project.py test_import_export.py test_full.py -q
echo "Core tests OK. Produce keygen-setup.exe on Windows: packaging\\build.bat"
