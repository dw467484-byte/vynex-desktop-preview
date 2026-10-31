#!/usr/bin/env bash
set -euo pipefail
SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${HOME}/.local/opt/vynex"
APPLICATIONS_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"
mkdir -p "$APP_DIR" "$APPLICATIONS_DIR" "$ICON_DIR"
cp -a "$SOURCE_DIR/." "$APP_DIR/"
chmod +x "$APP_DIR/VYNEX"
ICON_SOURCE="$APP_DIR/_internal/assets/VYNEX_icon.png"
if [[ ! -f "$ICON_SOURCE" ]]; then ICON_SOURCE="$APP_DIR/assets/VYNEX_icon.png"; fi
if [[ -f "$ICON_SOURCE" ]]; then cp "$ICON_SOURCE" "$ICON_DIR/vynex.png"; fi
escape_desktop_path() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/ /\\ /g'; }
EXEC_PATH="$(escape_desktop_path "$APP_DIR/VYNEX")"
ICON_PATH="$(escape_desktop_path "$ICON_DIR/vynex.png")"
cat > "$APPLICATIONS_DIR/vynex.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=VYNEX
Comment=Assistant IA local
Exec=$EXEC_PATH
Icon=$ICON_PATH
Terminal=false
Categories=Utility;Development;
StartupNotify=true
EOF
chmod 644 "$APPLICATIONS_DIR/vynex.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true; fi
echo "VYNEX est installé. Tu peux le trouver dans le menu des applications."
echo "Données utilisateur conservées dans ~/.local/share/vynex. Les modèles restent à installer séparément dans ~/VYNEXRuntime."
