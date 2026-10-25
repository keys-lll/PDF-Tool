from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QEventLoop, QPointF, QTimer, Qt
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import QApplication, QFileDialog, QListWidget
from pypdf import PdfReader

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from main_window import MainWindow  # noqa: E402
from platform_support import ui_font_family  # noqa: E402
from theme import build_stylesheet  # noqa: E402
from ui_pages import PAGE_REF_ROLE  # noqa: E402
from ui_widgets import PasswordDialog  # noqa: E402


def wait(milliseconds: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def drag_page(widget, source_row: int, target_row: int) -> None:
    """Simulate a real left-button drag through Qt's event system."""
    viewport = widget.viewport()
    start = QPointF(widget.visualItemRect(widget.item(source_row)).center())
    target = QPointF(widget.visualItemRect(widget.item(target_row)).center())

    def mouse_event(kind, position, button, buttons):
        return QMouseEvent(
            kind,
            position,
            QPointF(viewport.mapToGlobal(position.toPoint())),
            button,
            buttons,
            Qt.KeyboardModifier.NoModifier,
        )

    events = [
        mouse_event(
            QEvent.Type.MouseButtonPress,
            start,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
        ),
        mouse_event(
            QEvent.Type.MouseMove,
            start + QPointF(30, 0),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
        ),
        mouse_event(
            QEvent.Type.MouseMove,
            target,
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
        ),
        mouse_event(
            QEvent.Type.MouseButtonRelease,
            target,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
        ),
    ]
    for event in events:
        QApplication.sendEvent(viewport, event)
        wait(25)


class UiFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.app.setStyle("Fusion")
        family = ui_font_family()
        cls.app.setFont(QFont(family, 10))
        cls.app.setStyleSheet(build_stylesheet(family))

    def setUp(self) -> None:
        required = [
            PROJECT / "tests" / "samples" / "季度營運報告.pdf",
            PROJECT / "tests" / "samples" / "設計提案_首頁改版.pdf",
            PROJECT / "tests" / "samples" / "機密_董事會附件.pdf",
        ]
        if not all(path.exists() for path in required):
            self.skipTest("run tests/make_samples.py first")
        self.temp = tempfile.TemporaryDirectory(prefix="pdf-ui-test-")
        self.root = Path(self.temp.name)
        self.window = MainWindow()
        self.window.resize(1380, 900)
        self.window.show()
        wait(80)

    def tearDown(self) -> None:
        if self.window is not None:
            self.window.close()
            wait(30)
        self.temp.cleanup()

    def _wait_for_thumbnails(self, timeout: float = 15.0) -> None:
        deadline = time.monotonic() + timeout
        while self.window._thumbnail_workers and time.monotonic() < deadline:
            wait(50)
        self.assertFalse(self.window._thumbnail_workers, "thumbnail workers did not finish")

    def test_empty_state_and_controls(self) -> None:
        self.assertEqual(self.window.page_list.count(), 0)
        self.assertFalse(self.window.merge_button.isEnabled())
        self.assertEqual(self.window.content_stack.currentIndex(), 0)
        self.assertFalse(self.window.toolbar_widget.isVisible())
        self.assertTrue(self.window.empty_title.text())

    def test_progress_update_survives_completion_reentrancy(self) -> None:
        class ReentrantProgress:
            def __init__(self, window) -> None:
                self.window = window
                self.labels: list[str] = []
                self.values: list[int] = []

            def setMaximum(self, _value: int) -> None:
                pass

            def setLabelText(self, text: str) -> None:
                self.labels.append(text)

            def setValue(self, value: int) -> None:
                self.values.append(value)
                # QProgressDialog.setValue() processes events for modal
                # dialogs. Simulate the worker's queued completion arriving
                # and closing the dialog while setValue() is still running.
                self.window._finish_merge()

            def close(self) -> None:
                pass

            def deleteLater(self) -> None:
                pass

        progress = ReentrantProgress(self.window)
        self.window._merge_progress = progress
        self.window._merging = True
        self.window._on_merge_progress(1, 2)

        self.assertEqual(progress.labels, ["正在整理頁面… 1 / 2"])
        self.assertEqual(progress.values, [1])
        self.assertIsNone(self.window._merge_progress)
        self.assertFalse(self.window._merging)

    def test_add_reorder_and_remove_pages(self) -> None:
        report = PROJECT / "tests" / "samples" / "季度營運報告.pdf"
        design = PROJECT / "tests" / "samples" / "設計提案_首頁改版.pdf"
        self.window.add_paths([report, design])
        self._wait_for_thumbnails()

        self.assertEqual(self.window.page_list.count(), 7)
        self.assertTrue(self.window.merge_button.isEnabled())
        self.assertTrue(self.window.toolbar_widget.isVisible())
        self.assertEqual(self.window.content_stack.currentIndex(), 1)
        self.assertIn("7 頁", self.window.page_subtitle.text())
        self.assertEqual(self.window.page_list.dragDropMode(), QListWidget.DragDropMode.DropOnly)
        self.assertEqual(self.window.page_list.movement(), QListWidget.Movement.Snap)
        self.assertFalse(self.window.page_list.dragEnabled())
        self.assertTrue(self.window.page_list.acceptDrops())

        first_ref = self.window.page_list.item(0).data(PAGE_REF_ROLE)
        target_ref = self.window.page_list.item(3).data(PAGE_REF_ROLE)
        drag_page(self.window.page_list, 0, 3)
        self.assertEqual(self.window.page_list.item(3).data(PAGE_REF_ROLE), first_ref)
        self.assertEqual(self.window.page_list.item(2).data(PAGE_REF_ROLE), target_ref)
        self.assertEqual(self.window.page_list.currentRow(), 3)
        icons = [
            self.window.page_list.item(row).icon().isNull()
            for row in range(self.window.page_list.count())
        ]
        self.assertFalse(any(icons), "every page should have a thumbnail")

        original_first = self.window.page_list.item(0).data(PAGE_REF_ROLE)
        self.window.page_list.setCurrentRow(6)
        self.assertTrue(self.window.page_list.move_current(-6))
        moved = self.window.page_list.item(0).data(PAGE_REF_ROLE)
        self.assertEqual(moved.source_name, "設計提案_首頁改版.pdf")
        self.assertEqual(moved.page_index, 2)
        self.assertNotEqual(moved, original_first)

        self.window.page_list.clearSelection()
        self.window.page_list.item(0).setSelected(True)
        self.window._remove_selected_pages()
        self.assertEqual(self.window.page_list.count(), 6)
        self.assertIn("6 頁", self.window.page_subtitle.text())

    def test_password_dialog_validation(self) -> None:
        seen: list[str] = []

        def validator(password: str) -> tuple[bool, str]:
            seen.append(password)
            if password == "open123":
                return True, ""
            return False, "密碼不正確，請再試一次。"

        dialog = PasswordDialog("機密_董事會附件.pdf", validator, self.window)
        dialog.show()
        wait(30)
        dialog.input.setText("wrong")
        dialog.accept()
        wait(30)
        self.assertTrue(dialog.isVisible())
        self.assertTrue(dialog.error_label.isVisible())
        self.assertIn("密碼不正確", dialog.error_label.text())
        self.assertNotEqual(dialog.result(), PasswordDialog.DialogCode.Accepted)

        dialog.input.setText("open123")
        dialog.accept()
        wait(30)
        self.assertEqual(dialog.result(), PasswordDialog.DialogCode.Accepted)
        self.assertEqual(dialog.input.text(), "")
        self.assertEqual(seen, ["wrong", "open123"])

    def test_locked_source_flow_and_merge_through_ui(self) -> None:
        secret = PROJECT / "tests" / "samples" / "機密_董事會附件.pdf"
        report = PROJECT / "tests" / "samples" / "季度營運報告.pdf"
        design = PROJECT / "tests" / "samples" / "設計提案_首頁改版.pdf"

        # Simulate adding a locked source without opening the modal dialog.
        source = self.window.workspace.add_source(secret)
        self.window._add_source_row(source)
        with patch.object(self.window, "_prompt_for_password", return_value=None):
            self.window._analyze_source(source)
        self.window._update_state()

        self.assertEqual(source.status, "locked")
        self.assertTrue(self.window.notice_label.isVisible())
        self.assertIn("尚未解鎖", self.window.notice_label.text())
        self.assertIn("需要密碼", self.window._source_rows[source.id].meta_label.text())

        self.window.workspace.inspect(source, "open123")
        self.window._on_source_ready(source)
        self.assertEqual(source.status, "ready")
        self.assertEqual(self.window.page_list.count(), 2)
        self.assertFalse(self.window.notice_label.isVisible())
        self.assertIn("已解鎖", self.window._source_rows[source.id].meta_label.text())

        self.window.add_paths([report, design])
        self._wait_for_thumbnails()
        self.assertEqual(self.window.page_list.count(), 9)

        last_row = self.window.page_list.count() - 1
        self.window.page_list.setCurrentRow(last_row)
        self.assertTrue(self.window.page_list.move_current(-last_row))
        moved = self.window.page_list.item(0).data(PAGE_REF_ROLE)
        self.assertEqual(moved.source_name, "設計提案_首頁改版.pdf")
        self.assertEqual(moved.page_index, 2)

        output = self.root / "merged-by-ui.pdf"
        self.window._show_merge_success = lambda _path, _count: None
        with patch.object(
            QFileDialog,
            "getSaveFileName",
            return_value=(str(output), "PDF 檔案 (*.pdf)"),
        ):
            self.window.merge_and_save()
            deadline = time.monotonic() + 20
            while self.window._merging and time.monotonic() < deadline:
                wait(50)
        self.assertFalse(self.window._merging)
        self.assertTrue(output.exists(), "merge did not create an output file")
        reader = PdfReader(str(output))
        self.assertEqual(len(reader.pages), 9)
        first_text = reader.pages[0].extract_text() or ""
        self.assertIn("RECOMMENDATION", first_text)
        self.assertEqual(list(self.root.glob(".pdf-page-merger-*")), [])
        self.assertTrue(self.window.merge_button.isEnabled())


if __name__ == "__main__":
    unittest.main(verbosity=2)
