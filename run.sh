#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$APP_DIR"
PYTHON="$APP_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
    echo "首次啟動：建立 Python 環境…"
    python3 -m venv --system-site-packages "$APP_DIR/.venv"
fi

if ! "$PYTHON" -c "import PySide6, pypdf, cryptography, pypdfium2, PIL" >/dev/null 2>&1; then
    echo "首次啟動：安裝相依套件…"
    "$PYTHON" -m pip install --upgrade pip
    "$PYTHON" -m pip install -r "$APP_DIR/requirements.txt"
fi

if ! command -v pdftoppm >/dev/null 2>&1; then
    echo "提示：未安裝 poppler-utils，頁面縮圖將無法顯示，但仍可合併 PDF。" >&2
fi

exec "$PYTHON" "$APP_DIR/main.py" "$@"
