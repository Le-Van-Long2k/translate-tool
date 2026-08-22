#!/bin/bash

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/OCRTranslator.desktop"

mkdir -p "$DESKTOP_DIR"

cat > "$APP_DIR/OCRTranslator.desktop" <<EOF
[Desktop Entry]
Version=2.0
Type=Application
Name=OCR Translator
Comment=OCR Translation Tool
Exec=$APP_DIR/start.sh
Path=$APP_DIR
Icon=$APP_DIR/icon_app.png
Terminal=false
Categories=Utility;Graphics;
StartupNotify=true
StartupWMClass=main
EOF

rm -f "$DESKTOP_FILE"
cp "$APP_DIR/OCRTranslator.desktop" "$DESKTOP_FILE"

chmod +x "$DESKTOP_FILE"

gio set "$DESKTOP_FILE" metadata::trusted true

update-desktop-database "$DESKTOP_DIR"