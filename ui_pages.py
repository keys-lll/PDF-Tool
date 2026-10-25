"""The reorderable page thumbnail gallery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QListView,
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)


PAGE_REF_ROLE = Qt.ItemDataRole.UserRole + 1
THUMB_LOADING_ROLE = Qt.ItemDataRole.UserRole + 2

CARD_WIDTH = 200
CARD_HEIGHT = 282


@dataclass(frozen=True)
class PageRef:
    source_id: str
    page_index: int
    source_name: str


class PageCardDelegate(QStyledItemDelegate):
    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return QSize(CARD_WIDTH, CARD_HEIGHT)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        card = QRectF(option.rect).adjusted(6, 6, -6, -6)

        background = QColor("#F3F9F6") if selected else QColor("#FFFDF9")
        border = QColor("#218B80") if selected else QColor("#E5DED2")
        if hovered and not selected:
            border = QColor("#B8CEC8")
            background = QColor("#FFFEFA")

        painter.setPen(QPen(border, 2.0 if selected else 1.0))
        painter.setBrush(background)
        painter.drawRoundedRect(card, 12, 12)

        thumb_area = QRectF(
            card.left() + 9, card.top() + 9, card.width() - 18, 194
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#F1EEE7"))
        painter.drawRoundedRect(thumb_area, 8, 8)

        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if isinstance(icon, QIcon) and not icon.isNull():
            target = thumb_area.adjusted(7, 7, -7, -7)
            pixel_ratio = max(1.0, painter.device().devicePixelRatioF())
            requested = QSize(
                max(1, int(target.width() * pixel_ratio)),
                max(1, int(target.height() * pixel_ratio)),
            )
            pixmap = icon.pixmap(requested)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    requested,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                draw_width = scaled.width() / pixel_ratio
                draw_height = scaled.height() / pixel_ratio
                x = target.center().x() - draw_width / 2
                y = target.center().y() - draw_height / 2
                shadow = QRectF(x + 2, y + 3, draw_width, draw_height)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(15, 35, 31, 26))
                painter.drawRoundedRect(shadow, 3, 3)
                scaled.setDevicePixelRatio(pixel_ratio)
                painter.drawPixmap(QPointF(x, y), scaled)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(20, 40, 35, 28), 1))
                painter.drawRect(QRectF(x, y, draw_width, draw_height))
        else:
            loading = bool(index.data(THUMB_LOADING_ROLE))
            self._draw_placeholder(painter, thumb_area, loading)

        self._draw_number(painter, thumb_area, index.row() + 1)

        ref = index.data(PAGE_REF_ROLE)
        if isinstance(ref, PageRef):
            source_name = ref.source_name
            original_page = ref.page_index + 1
        else:
            source_name = ""
            original_page = index.row() + 1

        caption_left = card.left() + 12
        caption_width = card.width() - 24
        title_font = QFont("Noto Sans CJK TC")
        title_font.setPixelSize(12)
        title_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(QColor("#20433C") if selected else QColor("#2A3834"))
        metrics = QFontMetrics(title_font)
        title = metrics.elidedText(
            source_name, Qt.TextElideMode.ElideMiddle, int(caption_width)
        )
        painter.drawText(
            QRectF(caption_left, thumb_area.bottom() + 9, caption_width, 18),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            title,
        )

        meta_font = QFont("Noto Sans CJK TC")
        meta_font.setPixelSize(11)
        painter.setFont(meta_font)
        painter.setPen(QColor("#6D7B76"))
        painter.drawText(
            QRectF(caption_left, thumb_area.bottom() + 27, caption_width, 16),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"原第 {original_page} 頁",
        )
        painter.restore()

    def _draw_placeholder(
        self, painter: QPainter, area: QRectF, loading: bool
    ) -> None:
        page_height = area.height() - 38
        page_width = page_height * 0.71
        page = QRectF(0, 0, page_width, page_height)
        page.moveCenter(QPointF(area.center().x(), area.center().y() - 8))
        painter.setPen(QPen(QColor("#DDD6CA"), 1))
        painter.setBrush(QColor(255, 255, 255, 205))
        painter.drawRoundedRect(page, 3, 3)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#E5E0D6"))
        for index, width_ratio in enumerate((0.56, 0.42, 0.52, 0.30)):
            painter.drawRoundedRect(
                QRectF(
                    page.left() + page.width() * 0.18,
                    page.top() + page.height() * (0.25 + index * 0.10),
                    page.width() * width_ratio,
                    3,
                ),
                1.5,
                1.5,
            )

        font = QFont("Noto Sans CJK TC")
        font.setPixelSize(10)
        painter.setFont(font)
        painter.setPen(QColor("#9A9387"))
        painter.drawText(
            QRectF(
                area.left(),
                area.bottom() - 19,
                area.width(),
                16,
            ),
            Qt.AlignmentFlag.AlignCenter,
            "正在產生縮圖" if loading else "無法預覽縮圖",
        )

    def _draw_number(self, painter: QPainter, area: QRectF, number: int) -> None:
        font = QFont("Noto Sans CJK TC")
        font.setPixelSize(11)
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        text = str(number)
        badge_width = max(27, metrics.horizontalAdvance(text) + 16)
        badge = QRectF(area.left() + 8, area.top() + 8, badge_width, 21)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(16, 102, 94, 236))
        painter.drawRoundedRect(badge, 10.5, 10.5)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, text)


class PageListWidget(QListWidget):
    filesDropped = Signal(list)
    orderChanged = Signal()
    deleteRequested = Signal()
    moveRequested = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageList")
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Snap)
        self.setGridSize(QSize(CARD_WIDTH, CARD_HEIGHT))
        self.setUniformItemSizes(True)
        self.setSpacing(0)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setDragEnabled(False)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAutoScroll(True)
        self.setAutoScrollMargin(64)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setItemDelegate(PageCardDelegate(self))

        self._press_pos: QPoint | None = None
        self._press_row = -1
        self._drag_active = False
        self._drag_item: QListWidgetItem | None = None
        self._last_drag_pos = QPoint()
        self._auto_scroll_timer = QTimer(self)
        self._auto_scroll_timer.setInterval(40)
        self._auto_scroll_timer.timeout.connect(self._auto_scroll_step)

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            position = event.position().toPoint()
            index = self.indexAt(position)
            self._press_pos = position
            self._press_row = index.row() if index.isValid() else -1
            self._drag_active = False
            self._drag_item = None

    def mouseMoveEvent(self, event) -> None:
        position = event.position().toPoint()
        left_button = event.buttons() & Qt.MouseButton.LeftButton

        if self._press_pos is not None and left_button and self._press_row >= 0:
            moved = (position - self._press_pos).manhattanLength()
            if not self._drag_active and moved >= QApplication.startDragDistance():
                item = self.item(self._press_row)
                if item is not None:
                    self._drag_active = True
                    self._drag_item = item
                    self._last_drag_pos = position
                    self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                    self._auto_scroll_timer.start()

            if self._drag_active:
                self._last_drag_pos = position
                self._reorder_under_pointer(position)
                event.accept()
                return

        if not left_button:
            if self.indexAt(position).isValid():
                self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.viewport().unsetCursor()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_active:
            self._finish_drag()
            event.accept()
            return
        self._press_pos = None
        self._press_row = -1
        super().mouseReleaseEvent(event)

    def hideEvent(self, event) -> None:
        if self._drag_active:
            self._finish_drag(emit_change=False)
        super().hideEvent(event)

    def _reorder_under_pointer(self, position: QPoint) -> None:
        if self._drag_item is None:
            return
        index = self.indexAt(position)
        if not index.isValid():
            return
        current_row = self.row(self._drag_item)
        target_row = index.row()
        if current_row < 0 or target_row == current_row:
            return
        item = self.takeItem(current_row)
        if item is not self._drag_item:
            return
        self.insertItem(target_row, item)
        self.setCurrentItem(item)

    def _auto_scroll_step(self) -> None:
        if not self._drag_active:
            self._auto_scroll_timer.stop()
            return
        scroll_bar = self.verticalScrollBar()
        if scroll_bar.maximum() <= scroll_bar.minimum():
            return
        position = self._last_drag_pos
        margin = 38
        if position.y() < margin:
            scroll_bar.setValue(max(scroll_bar.minimum(), scroll_bar.value() - 24))
        elif position.y() > self.viewport().height() - margin:
            scroll_bar.setValue(min(scroll_bar.maximum(), scroll_bar.value() + 24))
        else:
            return
        self._reorder_under_pointer(position)

    def _finish_drag(self, emit_change: bool = True) -> None:
        self._auto_scroll_timer.stop()
        self.viewport().unsetCursor()
        self._press_pos = None
        self._press_row = -1
        self._drag_active = False
        self._drag_item = None
        if emit_change:
            self.orderChanged.emit()

    def _pdf_drop_paths(self, mime) -> list[str]:
        if not mime.hasUrls():
            return []
        paths = []
        for url in mime.urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.casefold() == ".pdf":
                paths.append(str(path))
        return paths

    def dragEnterEvent(self, event) -> None:
        if self._pdf_drop_paths(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if self._pdf_drop_paths(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        paths = self._pdf_drop_paths(event.mimeData())
        if paths:
            event.acceptProposedAction()
            self.filesDropped.emit(paths)
            return
        super().dropEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.deleteRequested.emit()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Up and event.modifiers() == Qt.KeyboardModifier.AltModifier:
            self.moveRequested.emit(-1)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Down and event.modifiers() == Qt.KeyboardModifier.AltModifier:
            self.moveRequested.emit(1)
            event.accept()
            return
        super().keyPressEvent(event)

    def move_current(self, delta: int) -> bool:
        row = self.currentRow()
        if row < 0:
            return False
        target = row + delta
        if target < 0 or target >= self.count():
            return False
        item = self.takeItem(row)
        self.insertItem(target, item)
        self.setCurrentItem(item)
        self.scrollToItem(item, QAbstractItemView.ScrollHint.EnsureVisible)
        self.orderChanged.emit()
        return True

    def page_item(self, ref: PageRef) -> QListWidgetItem:
        item = QListWidgetItem()
        item.setData(PAGE_REF_ROLE, ref)
        item.setData(THUMB_LOADING_ROLE, True)
        item.setSizeHint(QSize(CARD_WIDTH, CARD_HEIGHT))
        item.setToolTip(f"{ref.source_name}\n原始第 {ref.page_index + 1} 頁")
        return item
