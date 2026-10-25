#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APPS_DIR"
chmod +x "$APP_DIR/run.sh"

ENTRY="$APPS_DIR/pdf-page-merger.desktop"
cat > "$ENTRY" <<EOF
[Desktop Entry]
Type=Application
Name=PDF 併頁器
Comment=合併 PDF 並拖曳調整頁面順序
Exec="$APP_DIR/run.sh" %F
Path=$APP_DIR
Icon=$APP_DIR/assets/app_icon.svg
Terminal=false
Categories=Office;
MimeType=application/pdf;
StartupNotify=true
EOF
chmod +x "$ENTRY"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
fi

echo "已建立選單捷徑：$ENTRY"
echo "可從應用程式選單搜尋「PDF 併頁器」啟動。"
