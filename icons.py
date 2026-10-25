"""Small painted icons so the app has no external image dependencies."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)

from platform_support import ui_font_family

ACCENT = QColor("#0F766E")
DEEP_ACCENT = QColor("#115E59")


def _canvas(width: int, height: int) -> tuple[QPixmap, QPainter]:
    scale = 2
    pixmap = QPixmap(width * scale, height * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.scale(scale, scale)
    return pixmap, painter


def _finish(pixmap: QPixmap, painter: QPainter) -> QPixmap:
    painter.end()
    pixmap.setDevicePixelRatio(2.0)
    return pixmap


def _page_path(rect: QRectF, fold: float, radius: float) -> QPainterPath:
    x, y, width, height = rect.x(), rect.y(), rect.width(), rect.height()
    path = QPainterPath()
    path.moveTo(x + radius, y)
    path.lineTo(x + width - fold, y)
    path.lineTo(x + width, y + fold)
    path.lineTo(x + width, y + height - radius)
    path.quadTo(x + width, y + height, x + width - radius, y + height)
    path.lineTo(x + radius, y + height)
    path.quadTo(x, y + height, x, y + height - radius)
    path.lineTo(x, y + radius)
    path.quadTo(x, y, x + radius, y)
    path.closeSubpath()
    return path


def app_icon_pixmap(size: int) -> QPixmap:
    pixmap, painter = _canvas(size, size)
    scale = size / 128.0

    background = QLinearGradient(0, 0, size, size)
    background.setColorAt(0.0, QColor("#16857B"))
    background.setColorAt(1.0, DEEP_ACCENT)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(background)
    painter.drawRoundedRect(
        QRectF(2, 2, size - 4, size - 4), size * 0.23, size * 0.23
    )

    painter.setBrush(QColor(255, 255, 255, 24))
    painter.drawEllipse(QPointF(size * 0.18, size * 0.14), size * 0.42, size * 0.28)

    page_rect = QRectF(36 * scale, 23 * scale, 58 * scale, 76 * scale)
    page = _page_path(page_rect, 16 * scale, 7 * scale)
    painter.setBrush(QColor(0, 0, 0, 38))
    painter.drawPath(page.translated(2 * scale, 3 * scale))
    painter.setBrush(QColor("#FFFDF8"))
    painter.drawPath(page)

    fold = QPainterPath()
    fold.moveTo(page_rect.right() - 16 * scale, page_rect.top())
    fold.lineTo(page_rect.right(), page_rect.top() + 16 * scale)
    fold.lineTo(page_rect.right() - 16 * scale, page_rect.top() + 16 * scale)
    fold.closeSubpath()
    painter.setBrush(QColor("#CFE1DD"))
    painter.drawPath(fold)

    painter.setPen(
        QPen(ACCENT, 4.0 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    )
    line_y = page_rect.top() + 34 * scale
    for width in (32, 30, 21):
        painter.drawLine(
            QPointF(page_rect.left() + 12 * scale, line_y),
            QPointF(page_rect.left() + (12 + width) * scale, line_y),
        )
        line_y += 11 * scale

    badge_center = QPointF(94 * scale, 91 * scale)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#F2A65A"))
    painter.drawEllipse(badge_center, 17 * scale, 17 * scale)
    plus_pen = QPen(QColor("#FFFFFF"), 4.0 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(plus_pen)
    painter.drawLine(
        QPointF(badge_center.x() - 6 * scale, badge_center.y()),
        QPointF(badge_center.x() + 6 * scale, badge_center.y()),
    )
    painter.drawLine(
        QPointF(badge_center.x(), badge_center.y() - 6 * scale),
        QPointF(badge_center.x(), badge_center.y() + 6 * scale),
    )
    return _finish(pixmap, painter)


def app_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 96, 128, 256):
        icon.addPixmap(app_icon_pixmap(size))
    return icon


def pdf_badge_pixmap(height: int = 44) -> QPixmap:
    width = round(height * 0.76)
    pixmap, painter = _canvas(width, height)
    page_rect = QRectF(2, 2, width - 4, height - 4)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(0, 0, 0, 22))
    painter.drawRoundedRect(page_rect.translated(1, 2), 6, 6)
    badge = _page_path(page_rect, 10, 5)
    painter.setBrush(QColor("#D97757"))
    painter.drawPath(badge)

    fold = QPainterPath()
    fold.moveTo(page_rect.right() - 10, page_rect.top())
    fold.lineTo(page_rect.right(), page_rect.top() + 10)
    fold.lineTo(page_rect.right() - 10, page_rect.top() + 10)
    fold.closeSubpath()
    painter.setBrush(QColor("#B95D3F"))
    painter.drawPath(fold)

    font = QFont(ui_font_family())
    font.setPixelSize(max(6, round(height * 0.17)))
    font.setWeight(QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#FFFFFF"))
    painter.drawText(
        QRectF(2, height * 0.50, width - 4, height * 0.34),
        Qt.AlignmentFlag.AlignCenter,
        "PDF",
    )
    return _finish(pixmap, painter)


def lock_pixmap(size: int = 54) -> QPixmap:
    pixmap, painter = _canvas(size, size)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#F7E8D9"))
    painter.drawEllipse(QRectF(1, 1, size - 2, size - 2))

    body = QRectF(size * 0.31, size * 0.47, size * 0.38, size * 0.29)
    painter.setBrush(QColor("#B45309"))
    painter.drawRoundedRect(body, size * 0.06, size * 0.06)

    shackle = QPainterPath()
    shackle.moveTo(size * 0.38, size * 0.50)
    shackle.lineTo(size * 0.38, size * 0.40)
    shackle.cubicTo(
        size * 0.38,
        size * 0.24,
        size * 0.62,
        size * 0.24,
        size * 0.62,
        size * 0.40,
    )
    shackle.lineTo(size * 0.62, size * 0.50)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(
        QPen(QColor("#B45309"), size * 0.075, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    )
    painter.drawPath(shackle)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#FFF8EE"))
    painter.drawEllipse(QPointF(size * 0.50, size * 0.59), size * 0.035, size * 0.055)
    return _finish(pixmap, painter)


def empty_state_pixmap(width: int = 210, height: int = 170) -> QPixmap:
    pixmap, painter = _canvas(width, height)
    painter.setPen(QPen(QColor("#E1DACD"), 1.2))
    painter.setBrush(QColor("#EFE9DD"))
    painter.save()
    painter.translate(width * 0.53, height * 0.49)
    painter.rotate(8)
    painter.drawRoundedRect(QRectF(-41, -50, 82, 105), 7, 7)
    painter.restore()

    painter.save()
    painter.translate(width * 0.47, height * 0.50)
    painter.rotate(-7)
    painter.setBrush(QColor("#F8F4EB"))
    painter.drawRoundedRect(QRectF(-42, -51, 84, 106), 7, 7)
    painter.restore()

    painter.save()
    painter.translate(width * 0.50, height * 0.48)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(15, 35, 31, 25))
    painter.drawRoundedRect(QRectF(-36, -43, 82, 106), 8, 8)
    painter.setBrush(QColor("#FFFDF9"))
    painter.setPen(QPen(QColor("#D9D0C1"), 1.2))
    painter.drawRoundedRect(QRectF(-39, -48, 82, 106), 8, 8)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(ACCENT)
    painter.drawRoundedRect(QRectF(-25, -35, 35, 8), 4, 4)
    painter.setBrush(QColor("#D9E1DC"))
    for index, line_width in enumerate((53, 43, 49, 31)):
        painter.drawRoundedRect(QRectF(-25, -17 + index * 12, line_width, 4), 2, 2)

    painter.setBrush(QColor("#F2A65A"))
    painter.setPen(QPen(QColor("#FFFDF9"), 3))
    painter.drawEllipse(QPointF(43, 58), 18, 18)
    painter.setPen(
        QPen(QColor("#FFFFFF"), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    )
    painter.drawLine(QPointF(35, 58), QPointF(51, 58))
    painter.drawLine(QPointF(43, 50), QPointF(43, 66))
    painter.restore()
    return _finish(pixmap, painter)
