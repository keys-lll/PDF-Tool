"""Reusable widgets: source rows and the per-file password prompt."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from icons import lock_pixmap, pdf_badge_pixmap
from pdf_engine import PdfSource


class ElidedLabel(QLabel):
    """A label that shortens the middle of long text instead of resizing."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_text = text
        self._mode = Qt.TextElideMode.ElideMiddle
        self._refreshing = False
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(0)
        self.setAccessibleName(text)
        self._refresh()

    def setFullText(self, text: str) -> None:
        self._full_text = text
        self.setAccessibleName(text)
        self._refresh()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh()

    def _refresh(self) -> None:
        # setText() can synchronously trigger another layout/resize event.
        # Without this guard a long filename can recurse until Qt crashes.
        if self._refreshing:
            return
        width = max(0, self.contentsRect().width())
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self._full_text, self._mode, width)
        if elided == self.text():
            return
        self._refreshing = True
        try:
            super().setText(elided)
        finally:
            self._refreshing = False


class SourceRow(QFrame):
    unlockRequested = Signal(str)
    removeRequested = Signal(str)

    def __init__(self, source: PdfSource, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.source_id = source.id
        self._locked = False
        self.setObjectName("sourceRow")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFixedHeight(68)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 8, 8)
        layout.setSpacing(9)

        badge = pdf_badge_pixmap(38)
        self.icon_label = QLabel()
        self.icon_label.setPixmap(badge)
        self.icon_label.setFixedSize(29, 38)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        text_column = QVBoxLayout()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(2)
        self.name_label = ElidedLabel()
        self.name_label.setObjectName("sourceName")
        self.meta_label = ElidedLabel()
        self.meta_label.setObjectName("sourceMeta")
        text_column.addWidget(self.name_label)
        text_column.addWidget(self.meta_label)
        layout.addLayout(text_column, 1)

        self.unlock_button = QPushButton("解鎖")
        self.unlock_button.setObjectName("unlockButton")
        self.unlock_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.unlock_button.setFixedHeight(27)
        self.unlock_button.setToolTip("輸入這份 PDF 的開啟密碼")
        self.unlock_button.clicked.connect(
            lambda: self.unlockRequested.emit(self.source_id)
        )
        layout.addWidget(self.unlock_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self.remove_button = QPushButton("×")
        self.remove_button.setObjectName("removeSourceButton")
        self.remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_button.setFixedSize(23, 27)
        self.remove_button.setToolTip("從清單移除這份 PDF")
        self.remove_button.clicked.connect(
            lambda: self.removeRequested.emit(self.source_id)
        )
        layout.addWidget(self.remove_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self.update_source(source)

    def update_source(self, source: PdfSource) -> None:
        self.name_label.setFullText(source.name)
        self.name_label.setToolTip(str(source.path))
        self.setToolTip(str(source.path))
        self.setAccessibleName(source.name)
        self._locked = source.status == "locked"
        tone = "neutral"

        if source.status == "ready":
            prefix = "已解鎖 · " if source.encrypted else ""
            self.meta_label.setFullText(f"{prefix}{source.page_count} 頁")
            self.meta_label.setToolTip(
                f"{source.page_count} 頁"
                + ("，已使用密碼解鎖" if source.encrypted else "")
            )
            tone = "ready"
            self.unlock_button.hide()
        elif source.status == "locked":
            self.meta_label.setFullText("已加密 · 需要密碼")
            self.meta_label.setToolTip("按「解鎖」輸入密碼")
            tone = "locked"
            self.unlock_button.show()
        elif source.status == "error":
            self.meta_label.setFullText(source.error or "無法讀取")
            self.meta_label.setToolTip(source.error or "無法讀取")
            tone = "error"
            self.unlock_button.hide()
        else:
            self.meta_label.setFullText("讀取中…")
            self.meta_label.setToolTip("")
            self.unlock_button.hide()

        self.meta_label.setProperty("tone", tone)
        for widget in (self.meta_label, self):
            widget.setProperty("tone", tone)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

        self.remove_button.setAccessibleName(f"移除 {source.name}")
        self.unlock_button.setAccessibleName(f"解鎖 {source.name}")

    def mouseDoubleClickEvent(self, event) -> None:
        if self._locked:
            self.unlockRequested.emit(self.source_id)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class PasswordDialog(QDialog):
    """Collects and verifies a password without retaining it afterwards."""

    def __init__(
        self,
        file_name: str,
        validator: Callable[[str], tuple[bool, str]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._validator = validator
        self._busy = False
        self.setWindowTitle("需要 PDF 密碼")
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setModal(True)
        self.setFixedWidth(446)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 22)
        layout.setSpacing(0)

        lock_label = QLabel()
        lock_label.setPixmap(lock_pixmap(56))
        lock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lock_label)
        layout.addSpacing(10)

        title = QLabel("這份 PDF 已加密")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(8)

        file_label = QLabel(file_name)
        file_label.setObjectName("dialogFileName")
        file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_label.setWordWrap(True)
        layout.addWidget(file_label)
        layout.addSpacing(10)

        body = QLabel(
            "請輸入開啟密碼。密碼只會用於本次解鎖，不會儲存到磁碟。"
        )
        body.setObjectName("dialogBody")
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        layout.addWidget(body)
        layout.addSpacing(18)

        self.input = QLineEdit()
        self.input.setObjectName("passwordInput")
        self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setPlaceholderText("輸入 PDF 密碼")
        self.input.setClearButtonEnabled(True)
        self.input.returnPressed.connect(self.accept)
        layout.addWidget(self.input)
        layout.addSpacing(8)

        self.show_password = QCheckBox("顯示密碼")
        self.show_password.toggled.connect(self._toggle_password_visibility)
        layout.addWidget(self.show_password, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(9)

        self.error_label = QLabel()
        self.error_label.setObjectName("dialogError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        layout.addSpacing(16)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)
        button_row.addStretch(1)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.setMinimumWidth(88)
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_button)
        self.unlock_button = QPushButton("解鎖 PDF")
        self.unlock_button.setObjectName("primaryButton")
        self.unlock_button.setMinimumWidth(112)
        self.unlock_button.setFixedHeight(40)
        self.unlock_button.setDefault(True)
        self.unlock_button.clicked.connect(self.accept)
        button_row.addWidget(self.unlock_button)
        layout.addLayout(button_row)

        self.input.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def _toggle_password_visibility(self, visible: bool) -> None:
        self.input.setEchoMode(
            QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        )
        self.input.setFocus()

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()
        self.adjustSize()

    def accept(self) -> None:
        if self._busy:
            return
        password = self.input.text()
        if not password:
            self._show_error("請先輸入密碼。")
            self.input.setFocus()
            return

        self._show_error("")
        self.error_label.hide()
        self._busy = True
        self.input.setEnabled(False)
        self.show_password.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.unlock_button.setEnabled(False)
        self.unlock_button.setText("解鎖中…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            valid, message = self._validator(password)
        except Exception:
            valid = False
            message = "解鎖時發生錯誤，請再試一次。"
        finally:
            QApplication.restoreOverrideCursor()
            self._busy = False
            self.input.setEnabled(True)
            self.show_password.setEnabled(True)
            self.cancel_button.setEnabled(True)
            self.unlock_button.setEnabled(True)
            self.unlock_button.setText("解鎖 PDF")

        if not valid:
            self._show_error(message or "密碼不正確，請再試一次。")
            self.input.setFocus()
            self.input.selectAll()
            return

        self.input.clear()
        super().accept()

    def reject(self) -> None:
        if self._busy:
            return
        self.input.clear()
        super().reject()
