"""Main application window."""

from __future__ import annotations

import datetime
from pathlib import Path

from PySide6.QtCore import QThreadPool, Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from icons import app_icon, app_icon_pixmap, empty_state_pixmap, lock_pixmap
from pdf_engine import (
    IncorrectPassword,
    PageSpec,
    PasswordRequired,
    PdfSource,
    PdfWorkError,
    PdfWorkspace,
)
from ui_pages import PAGE_REF_ROLE, THUMB_LOADING_ROLE, PageListWidget, PageRef
from ui_widgets import PasswordDialog, SourceRow
from workers import MergeWorker, ThumbnailWorker

APP_NAME = "PDF 併頁器"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.resize(1380, 900)
        self.setMinimumSize(1040, 680)
        self.setAcceptDrops(True)

        self.workspace = PdfWorkspace()
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(3)
        self._source_rows: dict[str, SourceRow] = {}
        self._materialized_sources: set[str] = set()
        self._thumbnail_workers: dict[str, ThumbnailWorker] = {}
        self._merge_worker: MergeWorker | None = None
        self._merge_progress: QProgressDialog | None = None
        self._merging = False
        self._pending_merge_pages = 0
        self._closing = False
        self._last_dir = self._default_start_dir()
        self._last_output_dir: Path | None = None

        self._build_menu()
        self._build_ui()
        self._update_state()
        self.statusBar().showMessage(
            "拖入 PDF，或按「新增 PDF 檔案」開始。", 5000
        )

    # ------------------------------------------------------------------ setup

    def _default_start_dir(self) -> Path:
        documents = Path.home() / "Documents"
        return documents if documents.is_dir() else Path.home()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("檔案")
        self.add_action = QAction("新增 PDF…", self)
        self.add_action.setShortcut(QKeySequence("Ctrl+O"))
        self.add_action.triggered.connect(self.choose_files)
        file_menu.addAction(self.add_action)
        file_menu.addSeparator()

        self.merge_action = QAction("合併並儲存…", self)
        self.merge_action.setShortcut(QKeySequence("Ctrl+S"))
        self.merge_action.triggered.connect(self.merge_and_save)
        file_menu.addAction(self.merge_action)
        file_menu.addSeparator()

        quit_action = QAction("結束", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        edit_menu = self.menuBar().addMenu("編輯")
        self.move_up_action = QAction("上移目前頁面", self)
        self.move_up_action.setShortcut(QKeySequence("Alt+Up"))
        self.move_up_action.triggered.connect(lambda: self._move_current(-1))
        edit_menu.addAction(self.move_up_action)

        self.move_down_action = QAction("下移目前頁面", self)
        self.move_down_action.setShortcut(QKeySequence("Alt+Down"))
        self.move_down_action.triggered.connect(lambda: self._move_current(1))
        edit_menu.addAction(self.move_down_action)

        edit_menu.addSeparator()
        self.delete_action = QAction("移除選取頁面", self)
        self.delete_action.setShortcut(QKeySequence(Qt.Key.Key_Delete))
        self.delete_action.triggered.connect(self._remove_selected_pages)
        edit_menu.addAction(self.delete_action)

        help_menu = self.menuBar().addMenu("說明")
        about_action = QAction("關於 PDF 併頁器", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_content(), 1)

        self.statusBar().setSizeGripEnabled(False)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(330)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(22, 24, 22, 18)
        layout.setSpacing(0)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 0, 0)
        brand_row.setSpacing(11)
        brand_icon = QLabel()
        brand_icon.setPixmap(app_icon_pixmap(44))
        brand_icon.setFixedSize(44, 44)
        brand_row.addWidget(brand_icon)

        brand_text = QVBoxLayout()
        brand_text.setContentsMargins(0, 0, 0, 0)
        brand_text.setSpacing(1)
        brand_title = QLabel(APP_NAME)
        brand_title.setObjectName("brandTitle")
        brand_subtitle = QLabel("合併、排序，一次完成")
        brand_subtitle.setObjectName("brandSubtitle")
        brand_text.addWidget(brand_title)
        brand_text.addWidget(brand_subtitle)
        brand_row.addLayout(brand_text, 1)
        layout.addLayout(brand_row)
        layout.addSpacing(22)

        self.add_button = QPushButton("＋  新增 PDF 檔案")
        self.add_button.setObjectName("primaryButton")
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.setFixedHeight(44)
        self.add_button.clicked.connect(self.choose_files)
        layout.addWidget(self.add_button)

        hint = QLabel("或直接把 PDF 拖進視窗")
        hint.setObjectName("sideHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(hint)
        layout.addSpacing(18)

        rule = QFrame()
        rule.setObjectName("rule")
        layout.addWidget(rule)
        layout.addSpacing(15)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        section_title = QLabel("來源檔案")
        section_title.setObjectName("sectionTitle")
        header.addWidget(section_title)
        header.addStretch(1)
        self.source_count_chip = QLabel("0 份")
        self.source_count_chip.setObjectName("countChip")
        header.addWidget(self.source_count_chip)
        layout.addLayout(header)
        layout.addSpacing(10)

        self.source_scroll = QScrollArea()
        self.source_scroll.setWidgetResizable(True)
        self.source_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.source_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.source_container = QWidget()
        self.source_layout = QVBoxLayout(self.source_container)
        self.source_layout.setContentsMargins(0, 0, 2, 0)
        self.source_layout.setSpacing(8)
        self.source_empty = QLabel(
            "還沒有來源 PDF。\n用上方按鈕加入，或直接拖進來。"
        )
        self.source_empty.setObjectName("sourceEmpty")
        self.source_empty.setWordWrap(True)
        self.source_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.source_layout.addWidget(self.source_empty)
        self.source_layout.addStretch(1)
        self.source_scroll.setWidget(self.source_container)
        layout.addWidget(self.source_scroll, 1)

        layout.addSpacing(12)
        security = QFrame()
        security.setObjectName("securityCard")
        security_layout = QHBoxLayout(security)
        security_layout.setContentsMargins(10, 8, 10, 8)
        security_layout.setSpacing(8)
        lock_icon = QLabel()
        lock_icon.setPixmap(lock_pixmap(26))
        lock_icon.setFixedSize(26, 26)
        security_layout.addWidget(lock_icon, 0, Qt.AlignmentFlag.AlignTop)
        security_text = QVBoxLayout()
        security_text.setContentsMargins(0, 0, 0, 0)
        security_text.setSpacing(1)
        security_title = QLabel("密碼只在本次執行中使用")
        security_title.setObjectName("securityTitle")
        security_body = QLabel("解密暫存檔會在關閉程式後刪除。")
        security_body.setObjectName("securityBody")
        security_body.setWordWrap(True)
        security_text.addWidget(security_title)
        security_text.addWidget(security_body)
        security_layout.addLayout(security_text, 1)
        layout.addWidget(security)
        return sidebar

    def _build_content(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(32, 26, 32, 16)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(18)
        title_column = QVBoxLayout()
        title_column.setContentsMargins(0, 0, 0, 0)
        title_column.setSpacing(3)
        page_title = QLabel("頁面順序")
        page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel("尚未加入頁面")
        self.page_subtitle.setObjectName("pageSubtitle")
        title_column.addWidget(page_title)
        title_column.addWidget(self.page_subtitle)
        header.addLayout(title_column)
        header.addStretch(1)

        self.merge_button = QPushButton("合併並儲存…")
        self.merge_button.setObjectName("primaryButton")
        self.merge_button.setMinimumWidth(146)
        self.merge_button.setFixedHeight(44)
        self.merge_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.merge_button.clicked.connect(self.merge_and_save)
        header.addWidget(self.merge_button, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(header)

        self.notice_label = QLabel()
        self.notice_label.setObjectName("noticeLabel")
        self.notice_label.setWordWrap(True)
        self.notice_label.hide()
        notice_wrap = QVBoxLayout()
        notice_wrap.setContentsMargins(0, 14, 0, 0)
        notice_wrap.addWidget(self.notice_label)
        layout.addLayout(notice_wrap)

        self.toolbar_widget = QWidget()
        toolbar = QHBoxLayout(self.toolbar_widget)
        toolbar.setContentsMargins(0, 18, 0, 10)
        toolbar.setSpacing(5)
        self.page_hint = QLabel("拖曳縮圖調整順序 · Delete 移除選取頁面")
        self.page_hint.setObjectName("pageHint")
        toolbar.addWidget(self.page_hint)
        toolbar.addStretch(1)

        self.move_up_button = QPushButton("↑ 上移")
        self.move_up_button.setObjectName("ghostButton")
        self.move_up_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.move_up_button.setToolTip("把目前頁面往前移（Alt+↑）")
        self.move_up_button.clicked.connect(lambda: self._move_current(-1))
        toolbar.addWidget(self.move_up_button)

        self.move_down_button = QPushButton("↓ 下移")
        self.move_down_button.setObjectName("ghostButton")
        self.move_down_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.move_down_button.setToolTip("把目前頁面往後移（Alt+↓）")
        self.move_down_button.clicked.connect(lambda: self._move_current(1))
        toolbar.addWidget(self.move_down_button)

        self.remove_pages_button = QPushButton("移除選取")
        self.remove_pages_button.setObjectName("ghostButton")
        self.remove_pages_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_pages_button.setToolTip("移除選取的頁面（Delete）")
        self.remove_pages_button.clicked.connect(self._remove_selected_pages)
        toolbar.addWidget(self.remove_pages_button)
        layout.addWidget(self.toolbar_widget)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self._build_empty_state())
        self.page_list = PageListWidget()
        self.page_list.filesDropped.connect(self.add_paths)
        self.page_list.orderChanged.connect(self._on_order_changed)
        self.page_list.deleteRequested.connect(self._remove_selected_pages)
        self.page_list.moveRequested.connect(self._move_current)
        self.page_list.itemSelectionChanged.connect(self._sync_action_states)
        self.content_stack.addWidget(self.page_list)
        layout.addWidget(self.content_stack, 1)
        return panel

    def _build_empty_state(self) -> QWidget:
        empty = QWidget()
        layout = QVBoxLayout(empty)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        layout.addStretch(2)

        illustration = QLabel()
        illustration.setPixmap(empty_state_pixmap(210, 170))
        illustration.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(illustration)
        layout.addSpacing(4)

        eyebrow = QLabel("開始整理")
        eyebrow.setObjectName("emptyEyebrow")
        eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(eyebrow)
        layout.addSpacing(5)

        self.empty_title = QLabel("拖入 PDF，開始整理頁面")
        self.empty_title.setObjectName("emptyTitle")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_title)
        layout.addSpacing(9)

        self.empty_body = QLabel(
            "一次加入多份 PDF。拖曳縮圖調整順序；加密檔案會逐一詢問密碼。"
        )
        self.empty_body.setObjectName("emptyBody")
        self.empty_body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_body.setWordWrap(True)
        self.empty_body.setFixedWidth(470)
        self.empty_body.setMinimumHeight(52)
        layout.addWidget(
            self.empty_body, 0, Qt.AlignmentFlag.AlignHCenter
        )
        layout.addSpacing(20)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        choose_button = QPushButton("選擇 PDF 檔案")
        choose_button.setObjectName("secondaryButton")
        choose_button.setCursor(Qt.CursorShape.PointingHandCursor)
        choose_button.setFixedWidth(150)
        choose_button.clicked.connect(self.choose_files)
        button_row.addWidget(choose_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)
        layout.addStretch(3)
        return empty

    # --------------------------------------------------------------- files

    def choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "選擇 PDF 檔案",
            str(self._last_dir),
            "PDF 檔案 (*.pdf *.PDF)",
        )
        if paths:
            self.add_paths(paths)

    def add_paths(self, paths: list[str] | list[Path]) -> None:
        if self._merging:
            return
        valid: list[Path] = []
        rejected: list[str] = []
        for candidate in paths:
            path = Path(candidate).expanduser()
            if path.is_file() and path.suffix.casefold() == ".pdf":
                valid.append(path)
            else:
                rejected.append(path.name or str(path))
        if rejected:
            shown = "\n".join(f"• {name}" for name in rejected[:8])
            if len(rejected) > 8:
                shown += f"\n…另有 {len(rejected) - 8} 個檔案"
            QMessageBox.warning(
                self,
                "略過無法加入的檔案",
                f"只能加入存在的 PDF 檔案：\n\n{shown}",
            )
        if not valid:
            return

        added = 0
        for path in valid:
            try:
                source = self.workspace.add_source(path)
            except PdfWorkError as exc:
                QMessageBox.warning(
                    self, "無法加入檔案", f"{path.name}\n\n{exc}"
                )
                continue
            self._add_source_row(source)
            self._last_dir = path.parent
            added += 1
            self._analyze_source(source)
        self._update_state()
        if added:
            self.statusBar().showMessage(f"已加入 {added} 份 PDF。", 4000)

    def _add_source_row(self, source: PdfSource) -> None:
        row = SourceRow(source)
        row.unlockRequested.connect(self._unlock_source)
        row.removeRequested.connect(self._remove_source)
        self._source_rows[source.id] = row
        self.source_layout.insertWidget(self.source_layout.count() - 1, row)
        self.source_empty.hide()

    def _analyze_source(self, source: PdfSource) -> None:
        try:
            self.workspace.inspect(source)
        except PasswordRequired:
            self._refresh_source(source)
            self._prompt_for_password(source)
        except IncorrectPassword:
            self._refresh_source(source)
        except PdfWorkError as exc:
            self._refresh_source(source)
            QMessageBox.warning(
                self,
                "無法讀取 PDF",
                f"「{source.name}」\n\n{exc}",
            )
        else:
            self._on_source_ready(source)

    def _validate_password(self, source: PdfSource, password: str) -> tuple[bool, str]:
        try:
            self.workspace.inspect(source, password)
        except IncorrectPassword:
            self._refresh_source(source)
            return False, "密碼不正確，請再試一次。"
        except PasswordRequired:
            return False, "這份 PDF 需要密碼。"
        except PdfWorkError as exc:
            self._refresh_source(source)
            return False, str(exc)
        except Exception:
            return False, "解鎖時發生未預期的錯誤，請再試一次。"
        self._refresh_source(source)
        return True, ""

    def _prompt_for_password(self, source: PdfSource) -> None:
        dialog = PasswordDialog(
            source.name,
            lambda password: self._validate_password(source, password),
            self,
        )
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted and source.is_ready:
            self._on_source_ready(source)
            self.statusBar().showMessage(f"已解鎖「{source.name}」。", 3500)
        else:
            self._refresh_source(source)
            if source.status == "locked":
                self.statusBar().showMessage(
                    f"「{source.name}」維持鎖定，可稍後再解鎖。", 4500
                )
        self._update_state()

    def _unlock_source(self, source_id: str) -> None:
        source = self.workspace.sources.get(source_id)
        if source is not None and source.status == "locked":
            self._prompt_for_password(source)

    def _on_source_ready(self, source: PdfSource) -> None:
        if source.id in self._materialized_sources:
            self._refresh_source(source)
            self._update_state()
            return
        if not source.is_ready:
            return

        self.page_list.setUpdatesEnabled(False)
        first_item = None
        try:
            for page_index in range(source.page_count):
                ref = PageRef(source.id, page_index, source.name)
                item = self.page_list.page_item(ref)
                item.setData(
                    Qt.ItemDataRole.AccessibleTextRole,
                    f"{source.name}，第 {page_index + 1} 頁",
                )
                self.page_list.addItem(item)
                if first_item is None:
                    first_item = item
        finally:
            self.page_list.setUpdatesEnabled(True)

        self._materialized_sources.add(source.id)
        self._refresh_source(source)
        self._update_state()
        if first_item is not None:
            self.page_list.scrollToItem(first_item)
        self.statusBar().showMessage(
            f"「{source.name}」已加入 {source.page_count} 頁，正在製作縮圖…",
            4000,
        )
        self._start_thumbnail_worker(source)

    def _start_thumbnail_worker(self, source: PdfSource) -> None:
        if source.id in self._thumbnail_workers:
            return
        worker = ThumbnailWorker(self.workspace, source)
        worker.signals.finished.connect(self._on_thumbnails_ready)
        worker.signals.failed.connect(self._on_thumbnails_failed)
        self._thumbnail_workers[source.id] = worker
        self.pool.start(worker)

    def _on_thumbnails_ready(self, source_id: str, paths: object) -> None:
        self._thumbnail_workers.pop(source_id, None)
        if self._closing:
            return
        source = self.workspace.sources.get(source_id)
        if source is None or not isinstance(paths, list):
            return
        thumbnails = {index: str(path) for index, path in enumerate(paths)}
        for row in range(self.page_list.count()):
            item = self.page_list.item(row)
            ref = item.data(PAGE_REF_ROLE)
            if not isinstance(ref, PageRef) or ref.source_id != source_id:
                continue
            path = thumbnails.get(ref.page_index)
            if path:
                item.setIcon(QIcon(path))
            item.setData(THUMB_LOADING_ROLE, False)
        self.page_list.viewport().update()
        expected = 0
        loaded = 0
        for row in range(self.page_list.count()):
            item = self.page_list.item(row)
            ref = item.data(PAGE_REF_ROLE)
            if isinstance(ref, PageRef) and ref.source_id == source_id:
                expected += 1
                if ref.page_index in thumbnails:
                    loaded += 1
        if loaded == expected:
            self.statusBar().showMessage(
                f"「{source.name}」的縮圖已完成。", 2500
            )
        else:
            self.statusBar().showMessage(
                f"「{source.name}」有部分頁面無法產生縮圖，仍可合併。", 5000
            )

    def _on_thumbnails_failed(self, source_id: str, message: str) -> None:
        self._thumbnail_workers.pop(source_id, None)
        if self._closing:
            return
        source = self.workspace.sources.get(source_id)
        if source is None:
            return
        for row in range(self.page_list.count()):
            item = self.page_list.item(row)
            ref = item.data(PAGE_REF_ROLE)
            if isinstance(ref, PageRef) and ref.source_id == source_id:
                item.setData(THUMB_LOADING_ROLE, False)
                item.setToolTip(
                    f"{ref.source_name}\n原始第 {ref.page_index + 1} 頁\n無法產生縮圖"
                )
        self.page_list.viewport().update()
        self.statusBar().showMessage(message, 7000)

    def _refresh_source(self, source: PdfSource) -> None:
        row = self._source_rows.get(source.id)
        if row is not None:
            row.update_source(source)
        if len(self.workspace.sources) == 0:
            self.source_empty.show()
        else:
            self.source_empty.hide()

    def _remove_source(self, source_id: str) -> None:
        if self._merging:
            return
        source = self.workspace.sources.get(source_id)
        if source is None:
            return
        worker = self._thumbnail_workers.pop(source_id, None)
        if worker is not None:
            worker.cancel()
        removed = 0
        for row in range(self.page_list.count() - 1, -1, -1):
            item = self.page_list.item(row)
            ref = item.data(PAGE_REF_ROLE)
            if isinstance(ref, PageRef) and ref.source_id == source_id:
                self.page_list.takeItem(row)
                removed += 1
        row_widget = self._source_rows.pop(source_id, None)
        if row_widget is not None:
            row_widget.hide()
            row_widget.deleteLater()
        self._materialized_sources.discard(source_id)
        self.workspace.remove_source(source_id)
        if not self.workspace.sources:
            self.source_empty.show()
        self._update_state()
        self.statusBar().showMessage(
            f"已移除「{source.name}」與 {removed} 頁。", 3500
        )

    # --------------------------------------------------------------- gallery

    def _remove_selected_pages(self) -> None:
        if self._merging:
            return
        selected_rows = sorted(
            {index.row() for index in self.page_list.selectedIndexes()}
        )
        if not selected_rows:
            return
        first = selected_rows[0]
        for row in reversed(selected_rows):
            self.page_list.takeItem(row)
        if self.page_list.count():
            self.page_list.setCurrentRow(min(first, self.page_list.count() - 1))
        self._update_state()
        self.statusBar().showMessage(f"已移除 {len(selected_rows)} 頁。", 3000)

    def _move_current(self, delta: int) -> None:
        if self._merging:
            return
        if self.page_list.move_current(delta):
            self._sync_action_states()
            self.statusBar().showMessage("頁面順序已更新。", 1800)

    def _on_order_changed(self) -> None:
        self._sync_action_states()
        self.statusBar().showMessage("頁面順序已更新。", 1800)

    # --------------------------------------------------------------- state

    def _update_state(self) -> None:
        page_count = self.page_list.count()
        source_count = len(self.workspace.sources)
        self.source_count_chip.setText(f"{source_count} 份")
        self.source_empty.setVisible(source_count == 0)

        contributing = set()
        for row in range(page_count):
            ref = self.page_list.item(row).data(PAGE_REF_ROLE)
            if isinstance(ref, PageRef):
                contributing.add(ref.source_id)
        if page_count:
            self.page_subtitle.setText(
                f"共 {page_count} 頁 · 來自 {len(contributing)} 份 PDF"
            )
        elif source_count:
            self.page_subtitle.setText("尚未有可合併的頁面")
        else:
            self.page_subtitle.setText("尚未加入頁面")

        has_pages = page_count > 0
        self.content_stack.setCurrentIndex(1 if has_pages else 0)
        self.merge_button.setEnabled(has_pages and not self._merging)
        self.merge_action.setEnabled(has_pages and not self._merging)
        self.toolbar_widget.setVisible(has_pages)

        if source_count == 0:
            self.empty_title.setText("拖入 PDF，開始整理頁面")
            self.empty_body.setText(
                "一次加入多份 PDF。拖曳縮圖調整順序；加密檔案會逐一詢問密碼。"
            )
        else:
            self.empty_title.setText("目前沒有可合併的頁面")
            self.empty_body.setText(
                "請解鎖左側的加密 PDF，或加入其他檔案。"
            )

        locked = [
            source for source in self.workspace.sources.values()
            if source.status == "locked"
        ]
        errors = [
            source for source in self.workspace.sources.values()
            if source.status == "error"
        ]
        notices = []
        if locked:
            notices.append(
                f"有 {len(locked)} 份 PDF 尚未解鎖，其頁面不會被合併。"
                "請在左側按「解鎖」輸入密碼。"
            )
        if errors:
            notices.append(f"有 {len(errors)} 份 PDF 讀取失敗，請查看左側來源清單。")
        self.notice_label.setText("　".join(notices))
        self.notice_label.setVisible(bool(notices))
        self._sync_action_states()

    def _sync_action_states(self) -> None:
        selected = bool(self.page_list.selectedItems())
        current = self.page_list.currentRow()
        can_up = current > 0
        can_down = 0 <= current < self.page_list.count() - 1
        self.move_up_button.setEnabled(can_up and not self._merging)
        self.move_down_button.setEnabled(can_down and not self._merging)
        self.remove_pages_button.setEnabled(selected and not self._merging)
        self.move_up_action.setEnabled(can_up and not self._merging)
        self.move_down_action.setEnabled(can_down and not self._merging)
        self.delete_action.setEnabled(selected and not self._merging)

    # --------------------------------------------------------------- merge

    def _locked_confirmation(self) -> bool:
        locked = [
            source for source in self.workspace.sources.values()
            if source.status == "locked"
        ]
        if not locked:
            return True
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("尚有 PDF 未解鎖")
        box.setText(f"有 {len(locked)} 份 PDF 尚未解鎖")
        box.setInformativeText("這些 PDF 的頁面不會被合併。要繼續嗎？")
        continue_button = box.addButton(
            "繼續合併", QMessageBox.ButtonRole.AcceptRole
        )
        box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(continue_button)
        box.exec()
        return box.clickedButton() is continue_button

    def _collect_specs(self) -> list[PageSpec] | None:
        specs: list[PageSpec] = []
        for row in range(self.page_list.count()):
            item = self.page_list.item(row)
            ref = item.data(PAGE_REF_ROLE)
            if not isinstance(ref, PageRef):
                continue
            source = self.workspace.sources.get(ref.source_id)
            if source is None or not source.is_ready or source.working_path is None:
                QMessageBox.warning(
                    self,
                    "來源已失效",
                    "有頁面的來源 PDF 已失效，請重新加入檔案。",
                )
                return None
            specs.append(
                PageSpec(
                    source_path=source.working_path,
                    page_index=ref.page_index,
                    source_name=source.name,
                )
            )
        return specs

    def _default_output_path(self) -> Path:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = self._last_output_dir
        if folder is None or not folder.is_dir():
            first_source = next(iter(self.workspace.sources.values()), None)
            folder = (
                first_source.path.parent
                if first_source is not None
                else self._last_dir
            )
        return folder / f"合併文件_{stamp}.pdf"

    def merge_and_save(self) -> None:
        if self._merging or self.page_list.count() == 0:
            return
        if not self._locked_confirmation():
            return
        specs = self._collect_specs()
        if not specs:
            return

        chosen, _ = QFileDialog.getSaveFileName(
            self,
            "儲存合併後的 PDF",
            str(self._default_output_path()),
            "PDF 檔案 (*.pdf)",
        )
        if not chosen:
            return
        output = Path(chosen).expanduser()
        if output.suffix.casefold() != ".pdf":
            output = output.with_name(output.name + ".pdf")
        output_resolved = output.resolve()
        for source in self.workspace.sources.values():
            if source.path.resolve() == output_resolved:
                QMessageBox.warning(
                    self,
                    "不能覆蓋來源 PDF",
                    "請選擇不同的檔名，避免覆蓋原始檔案。",
                )
                return
            if (
                source.working_path is not None
                and source.working_path.resolve() == output_resolved
            ):
                QMessageBox.warning(
                    self,
                    "不能覆蓋工作檔案",
                    "請選擇不同的儲存位置。",
                )
                return

        self._start_merge(specs, output)

    def _start_merge(self, specs: list[PageSpec], output: Path) -> None:
        self._merging = True
        self._pending_merge_pages = len(specs)
        self._update_state()

        progress = QProgressDialog(
            "正在準備合併…", "取消", 0, len(specs), self
        )
        progress.setWindowTitle("合併 PDF")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.setMinimumWidth(430)
        progress.setValue(0)
        progress.show()

        worker = MergeWorker(specs, output)
        self._merge_worker = worker
        self._merge_progress = progress
        progress.canceled.connect(self._cancel_merge)
        worker.signals.progress.connect(self._on_merge_progress)
        worker.signals.succeeded.connect(self._on_merge_succeeded)
        worker.signals.failed.connect(self._on_merge_failed)
        worker.signals.cancelled.connect(self._on_merge_cancelled)
        self.pool.start(worker)

    def _on_merge_progress(self, current: int, total: int) -> None:
        if self._merge_progress is None:
            return
        self._merge_progress.setMaximum(total)
        self._merge_progress.setValue(current)
        if current < total:
            self._merge_progress.setLabelText(
                f"正在整理頁面… {current} / {total}"
            )
        else:
            self._merge_progress.setLabelText("正在寫入 PDF…")

    def _cancel_merge(self) -> None:
        if self._merge_worker is None:
            return
        self._merge_worker.cancel()
        if self._merge_progress is not None:
            self._merge_progress.setLabelText("正在取消合併…")
            self._merge_progress.setCancelButton(None)

    def _finish_merge(self) -> None:
        if self._merge_progress is not None:
            self._merge_progress.close()
            self._merge_progress.deleteLater()
            self._merge_progress = None
        self._merge_worker = None
        self._merging = False
        self._update_state()

    def _on_merge_succeeded(self, output: str) -> None:
        page_count = self._pending_merge_pages
        path = Path(output)
        self._last_output_dir = path.parent
        self._finish_merge()
        self.statusBar().showMessage(f"已儲存「{path.name}」。", 6000)
        self._show_merge_success(path, page_count)

    def _on_merge_failed(self, message: str) -> None:
        self._finish_merge()
        QMessageBox.critical(self, "合併失敗", message)
        self.statusBar().showMessage("合併失敗，未產生輸出檔。", 5000)

    def _on_merge_cancelled(self) -> None:
        self._finish_merge()
        self.statusBar().showMessage("已取消合併。", 3500)

    def _show_merge_success(self, path: Path, page_count: int) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("合併完成")
        box.setText(f"已合併 {page_count} 頁")
        box.setInformativeText(str(path))
        open_button = box.addButton(
            "開啟 PDF", QMessageBox.ButtonRole.AcceptRole
        )
        folder_button = box.addButton(
            "開啟資料夾", QMessageBox.ButtonRole.ActionRole
        )
        box.addButton("完成", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(open_button)
        box.exec()
        clicked = box.clickedButton()
        if clicked is open_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        elif clicked is folder_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))

    # --------------------------------------------------------------- misc

    def _pdf_paths_from_mime(self, mime) -> list[str]:
        paths = []
        if not mime.hasUrls():
            return paths
        for url in mime.urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.casefold() == ".pdf":
                paths.append(str(path))
        return paths

    def dragEnterEvent(self, event) -> None:
        if self._pdf_paths_from_mime(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if self._pdf_paths_from_mime(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        paths = self._pdf_paths_from_mime(event.mimeData())
        if paths:
            event.acceptProposedAction()
            self.add_paths(paths)
            return
        super().dropEvent(event)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            f"關於 {APP_NAME}",
            (
                f"<h3>{APP_NAME}</h3>"
                "<p>把多份 PDF 的頁面合併成一份，拖曳縮圖就能調整頁序。</p>"
                "<ul>"
                "<li>加密 PDF 會逐份詢問密碼，密碼不會儲存。</li>"
                "<li>解密暫存檔與縮圖會在工作階段結束後刪除。</li>"
                "<li>合併結果不保留書籤、表單欄位與附件。</li>"
                "</ul>"
                "<p>使用 PySide6 與 pypdf 製作。</p>"
            ),
        )

    def closeEvent(self, event) -> None:
        if self._merging:
            QMessageBox.information(
                self,
                "仍在合併",
                "請先取消目前的合併工作，再關閉程式。",
            )
            event.ignore()
            return
        self._closing = True
        for worker in list(self._thumbnail_workers.values()):
            worker.cancel()
        self._thumbnail_workers.clear()
        self.pool.clear()
        self.pool.waitForDone(3500)
        self.workspace.close()
        super().closeEvent(event)
