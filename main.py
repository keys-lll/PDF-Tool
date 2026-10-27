#!/usr/bin/env python3
"""Entry point for the PDF page merger desktop application."""

from __future__ import annotations

import sys
import traceback

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QApplication, QMessageBox

from main_window import APP_NAME, MainWindow
from platform_support import ui_font_family
from theme import build_stylesheet

SMOKE_TEST = "--smoke-test" in sys.argv


def _install_exception_hook() -> None:
    def report(exc_type, exc, tb) -> None:
        try:
            if sys.stderr is not None:
                sys.stderr.write("".join(traceback.format_exception(exc_type, exc, tb)))
                sys.stderr.flush()
        except Exception:
            pass
        QMessageBox.critical(
            None,
            "發生未預期的錯誤",
            f"程式發生未預期的錯誤，請重新啟動。\n\n{exc_type.__name__}: {exc}",
        )

    sys.excepthook = report


def _run_smoke_test() -> int:
    """Verify the frozen app can import Qt and render a PDF thumbnail.

    Used by the Windows CI build. No window is created and stdout is not
    required, so this also works in a --windowed PyInstaller executable.
    """
    import tempfile
    from pathlib import Path

    from pypdf import PdfWriter

    from pdf_engine import PdfWorkspace

    try:
        with tempfile.TemporaryDirectory(prefix="pdf-page-merger-smoke-") as temp:
            pdf_path = Path(temp) / "smoke.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=280)
            with open(pdf_path, "wb") as stream:
                writer.write(stream)

            workspace = PdfWorkspace()
            try:
                source = workspace.add_source(pdf_path)
                workspace.inspect(source)
                pages = workspace.render_thumbnails(
                    source, width=96, backend="pdfium"
                )
                if len(pages) != 1:
                    return 2
                if not pages[0].is_file() or pages[0].stat().st_size < 100:
                    return 2
            finally:
                workspace.close()
    except Exception:
        return 1
    return 0


def main() -> int:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    if SMOKE_TEST:
        return _run_smoke_test()
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion("1.1.1")
    app.setDesktopFileName("pdf-page-merger")
    app.setStyle("Fusion")
    font_family = ui_font_family()
    app.setFont(QFont(font_family, 10))
    app.setStyleSheet(build_stylesheet(font_family))
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
