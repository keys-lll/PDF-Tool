"""Small platform-specific presentation choices."""

from __future__ import annotations

import sys


def ui_font_family() -> str:
    if sys.platform.startswith("win"):
        return "Microsoft JhengHei UI"
    if sys.platform == "darwin":
        return "PingFang TC"
    return "Noto Sans CJK TC"
