#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" != "--yes" ]]; then
  echo "Cette opération supprime l'application et son raccourci, mais conserve les conversations et modèles locaux."
  read -r -p "Désinstaller VYNEX ? [o/N] " ANSWER
  [[ "$ANSWER" =~ ^([oO]|[oO][uU][iI]|[yY]|[yY][eE][sS])$ ]] || { echo "Annulé."; exit 0; }
fi
rm -rf "$HOME/.local/opt/vynex"
rm -f "$HOME/.local/share/applications/vynex.desktop"
rm -f "$HOME/.local/share/icons/hicolor/256x256/apps/vynex.png"
if command -v update-desktop-database >/dev/null 2>&1; then update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true; fi
echo "VYNEX a été désinstallé. Les conversations et modèles locaux ont été conservés."
