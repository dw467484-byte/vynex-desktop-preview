#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 est requis. Installe Python 3.10+ puis relance." >&2
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
VENV="$ROOT/.venv-macos-build"
DIST="$ROOT/dist_release_$STAMP"
BUILD="$ROOT/build_release_$STAMP"
SPEC="$ROOT/spec_release_$STAMP"
ARCH="$(uname -m)"
BASE_PYTHON="$(command -v python3)"
if ! "$BASE_PYTHON" -c 'import tkinter' >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installation de Python 3.12 avec Tkinter depuis Homebrew..."
    brew install python@3.12 python-tk@3.12
    BASE_PYTHON="$(brew --prefix python@3.12)/bin/python3.12"
  else
    echo "Tkinter manque à Python. Installe Python/Tkinter, ou Homebrew puis python@3.12 et python-tk@3.12." >&2
    exit 1
  fi
fi
"$BASE_PYTHON" -c 'import tkinter; print("Tkinter", tkinter.TkVersion)'
if [[ ! -x "$VENV/bin/python" ]] || ! "$VENV/bin/python" -c 'import tkinter' >/dev/null 2>&1; then
  # Recreate only this dedicated build virtualenv if it was made with Python without Tk.
  rm -rf "$VENV"
  "$BASE_PYTHON" -m venv --system-site-packages "$VENV"
fi
PY="$VENV/bin/python"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements-build.txt
"$PY" -m py_compile VYNEX.py
"$PY" -m unittest discover -s tests -v
"$PY" -m PyInstaller --noconfirm --clean --distpath "$DIST" --workpath "$BUILD" --specpath "$SPEC" VYNEX_macos.spec
APP="$DIST/VYNEX.app"
if [[ ! -d "$APP" ]]; then echo "Le bundle macOS VYNEX.app n'a pas été créé." >&2; exit 1; fi
/usr/libexec/PlistBuddy -c 'Print :NSMicrophoneUsageDescription' "$APP/Contents/Info.plist" >/dev/null
/usr/libexec/PlistBuddy -c 'Print :NSScreenCaptureUsageDescription' "$APP/Contents/Info.plist" >/dev/null
ARCHIVE="$ROOT/VYNEX-macos-${ARCH}-${STAMP}.zip"
ditto -c -k --sequesterRsrc --keepParent "$APP" "$ARCHIVE"
echo "SUCCÈS : $APP"
echo "Archive : $ARCHIVE"
echo "Attention : l'app n'est pas signée ni notariée par Apple dans ce script." 
