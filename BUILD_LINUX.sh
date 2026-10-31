#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 est requis." >&2
  exit 1
fi
if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
  echo "Tkinter n'est pas installé. Sur Ubuntu/Debian, exécute : sudo apt install python3-tk python3-venv python3-pip" >&2
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
VENV="$ROOT/.venv-linux-build"
DIST="$ROOT/dist_release_$STAMP"
BUILD="$ROOT/build_release_$STAMP"
SPEC="$ROOT/spec_release_$STAMP"
if [[ ! -x "$VENV/bin/python" ]]; then python3 -m venv "$VENV"; fi
PY="$VENV/bin/python"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements-build.txt
"$PY" -m py_compile VYNEX.py
"$PY" -m unittest discover -s tests -v
"$PY" -m PyInstaller --noconfirm --clean --onedir --windowed --name VYNEX --add-data "assets:assets" --distpath "$DIST" --workpath "$BUILD" --specpath "$SPEC" VYNEX.py
BUNDLE="$DIST/VYNEX"
if [[ ! -x "$BUNDLE/VYNEX" ]]; then echo "Le binaire Linux VYNEX n'a pas été créé." >&2; exit 1; fi
cp "$ROOT/install-linux.sh" "$BUNDLE/install-linux.sh"
cp "$ROOT/uninstall-linux.sh" "$BUNDLE/uninstall-linux.sh"
chmod +x "$BUNDLE/install-linux.sh" "$BUNDLE/uninstall-linux.sh" "$BUNDLE/VYNEX"
ARCHIVE="$ROOT/VYNEX-linux-x64-${STAMP}.tar.gz"
tar -czf "$ARCHIVE" -C "$DIST" VYNEX
echo "SUCCÈS : $BUNDLE/VYNEX"
echo "Archive : $ARCHIVE"
