#!/usr/bin/env python3
"""Entry point for the PDF page merger desktop application."""

from __future__ import annotations

import sys
import traceback

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QApplication, QMessageBox

from main_window import APP_NAME, MainWindow
from theme import APP_STYLE


def _install_exception_hook() -> None:
    def report(exc_type, exc, tb) -> None:
        traceback.print_exception(exc_type, exc, tb)
        QMessageBox.critical(
            None,
            "發生未預期的錯誤",
            f"程式發生未預期的錯誤，請重新啟動。\n\n{exc_type.__name__}: {exc}",
        )

    sys.excepthook = report


def main() -> int:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion("1.0.1")
    app.setDesktopFileName("pdf-page-merger")
    app.setStyle("Fusion")
    app.setFont(QFont("Noto Sans CJK TC", 10))
    app.setStyleSheet(APP_STYLE)
    _install_exception_hook()

    window = MainWindow()
    window.show()
    pdf_arguments = [
        argument
        for argument in sys.argv[1:]
        if argument.casefold().endswith(".pdf")
    ]
    if pdf_arguments:
        QTimer.singleShot(0, lambda: window.add_paths(pdf_arguments))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
