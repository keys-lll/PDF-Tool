#!/usr/bin/env python3
"""Generate sample PDFs used by the GUI smoke test and screenshots."""

from __future__ import annotations

import gc
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPageSize,
    QPainter,
    QPen,
    QPdfWriter,
)
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader, PdfWriter

PROJECT = Path(__file__).resolve().parent.parent
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from platform_support import ui_font_family

W, H = 1190, 1684
CREAM = QColor("#F8F5EE")
INK = QColor("#1E3630")
MUTED = QColor("#727B74")
TEAL = QColor("#0F766E")
TEAL_DARK = QColor("#115E59")
CORAL = QColor("#D97757")
AMBER = QColor("#E8A24B")
LINE = QColor("#DDD6C9")


def font(size: int, weight: QFont.Weight = QFont.Weight.Normal, family: str | None = None):
    value = QFont(family or ui_font_family())
    value.setPixelSize(size)
    value.setWeight(weight)
    return value


def text(p: QPainter, rect: QRectF, value: str, *, size=30, color=INK, weight=QFont.Weight.Normal, align=Qt.AlignmentFlag.AlignLeft):
    p.setFont(font(size, weight))
    p.setPen(color)
    p.drawText(rect, align | Qt.AlignmentFlag.AlignTop, value)


def rounded(p: QPainter, rect: QRectF, color, radius=24):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color if isinstance(color, QColor) else QBrush(color))
    p.drawRoundedRect(rect, radius, radius)


def base_page(p: QPainter, number: int, total: int, section: str) -> None:
    p.fillRect(QRectF(0, 0, W, H), CREAM)
    p.setFont(font(19, QFont.Weight.DemiBold))
    p.setPen(MUTED)
    p.drawText(QRectF(76, 55, 600, 30), Qt.AlignmentFlag.AlignLeft, "NORTHWIND / STUDIO")
    p.setFont(font(19))
    p.setPen(QColor("#9A9184"))
    p.drawText(
        QRectF(W - 330, 55, 254, 30),
        Qt.AlignmentFlag.AlignRight,
        section,
    )
    p.setPen(QPen(LINE, 1))
    p.drawLine(QPointF(76, H - 78), QPointF(W - 76, H - 78))
    p.setFont(font(18))
    p.setPen(QColor("#9A9184"))
    p.drawText(QRectF(76, H - 58, 350, 24), Qt.AlignmentFlag.AlignLeft, "內部使用 · 2026")
    p.drawText(
        QRectF(W - 220, H - 58, 144, 24),
        Qt.AlignmentFlag.AlignRight,
        f"{number:02d} / {total:02d}",
    )


def draw_report_cover(p: QPainter) -> None:
    p.fillRect(QRectF(0, 0, W, H), CREAM)
    rounded(p, QRectF(74, 70, 64, 64), TEAL, 18)
    text(p, QRectF(158, 80, 600, 44), "季度營運報告", size=26, color=TEAL, weight=QFont.Weight.DemiBold)
    text(
        p,
        QRectF(74, 360, 700, 340),
        "2026\n第四季回顧",
        size=132,
        color=INK,
        weight=QFont.Weight.Bold,
    )
    p.setPen(QPen(TEAL, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(82, 735), QPointF(218, 735))
    text(
        p,
        QRectF(76, 780, 620, 120),
        "把成長軌跡、客戶洞察與下一季行動\n整理成一個清楚的節奏。",
        size=33,
        color=MUTED,
    )
    panel = QRectF(755, 92, 360, 640)
    gradient = QLinearGradient(panel.topLeft(), panel.bottomRight())
    gradient.setColorAt(0, QColor("#16857B"))
    gradient.setColorAt(1, TEAL_DARK)
    rounded(p, panel, gradient, 30)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 30))
    p.drawEllipse(QPointF(1040, 220), 170, 170)
    p.setBrush(QColor(255, 255, 255, 22))
    p.drawEllipse(QPointF(840, 520), 210, 210)
    p.setPen(QPen(QColor(255, 255, 255, 150), 2))
    for offset, ratio in enumerate((0.55, 0.72, 0.44, 0.83, 0.67)):
        bar_h = 240 * ratio
        bar = QRectF(816 + offset * 54, 600 - bar_h, 30, bar_h)
        p.setBrush(QColor(255, 255, 255, 205))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(bar, 8, 8)
    p.setPen(QPen(QColor(255, 255, 255, 55), 1))
    p.drawLine(QPointF(816, 610), QPointF(1054, 610))
    text(
        p,
        QRectF(795, 640, 290, 50),
        "REVENUE +18.4%",
        size=22,
        color=QColor("#E8F7F2"),
        weight=QFont.Weight.DemiBold,
    )
    text(p, QRectF(76, H - 210, 640, 100), "準備者：策略與營運組\n2026 年 10 月", size=25, color=MUTED)


def draw_report_chart(p: QPainter) -> None:
    base_page(p, 2, 4, "營運回顧")
    text(p, QRectF(76, 155, 640, 66), "營收走過低谷，\n第四季回到成長線。", size=57, weight=QFont.Weight.Bold)
    text(p, QRectF(76, 305, 500, 40), "每月合併營收 · 單位：百萬元", size=24, color=MUTED)
    chart = QRectF(76, 405, 1038, 700)
    rounded(p, chart, QColor("#FFFDF9"), 26)
    p.setPen(QPen(QColor("#ECE6DB"), 1))
    for index in range(5):
        y = chart.top() + 110 + index * 120
        p.drawLine(QPointF(chart.left() + 95, y), QPointF(chart.right() - 45, y))
        text(
            p,
            QRectF(chart.left() + 32, y - 20, 46, 30),
            str(90 - index * 15),
            size=18,
            color=QColor("#A49C90"),
            align=Qt.AlignmentFlag.AlignRight,
        )
    values = (0.38, 0.44, 0.37, 0.52, 0.58, 0.63, 0.72, 0.69, 0.84, 0.92)
    months = ("1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月")
    available = chart.width() - 190
    step = available / len(values)
    for index, (value, month) in enumerate(zip(values, months)):
        height = value * 480
        x = chart.left() + 100 + index * step + step * 0.18
        width = step * 0.54
        color = CORAL if index == len(values) - 1 else TEAL
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawRoundedRect(QRectF(x, chart.bottom() - 92 - height, width, height), 8, 8)
        text(
            p,
            QRectF(x - 12, chart.bottom() - 78, width + 24, 26),
            month,
            size=17,
            color=MUTED,
            align=Qt.AlignmentFlag.AlignHCenter,
        )
    text(p, QRectF(76, 1160, 640, 44), "10 月為目前高點，較年初成長 32%。", size=26, color=TEAL_DARK, weight=QFont.Weight.DemiBold)
    p.setPen(QPen(LINE, 1))
    p.drawLine(QPointF(76, 1235), QPointF(1114, 1235))
    text(p, QRectF(76, 1265, 310, 40), "備註", size=21, color=MUTED, weight=QFont.Weight.DemiBold)
    text(p, QRectF(76, 1305, 960, 100), "以上數字為管理帳口徑，未經會計師查核。", size=23, color=MUTED)


def draw_report_metrics(p: QPainter) -> None:
    base_page(p, 3, 4, "關鍵指標")
    text(p, QRectF(76, 155, 800, 72), "三件事，讓這一季站穩。", size=62, weight=QFont.Weight.Bold)
    cards = [
        ("+18.4%", "營收成長", "較上一季回升，主要來自續約與進階方案。", TEAL),
        ("92%", "客戶留存", "企業客群留存創新高，導入速度同步改善。", CORAL),
        ("3.1×", "內容效率", "設計與內容產線重整後的平均產出倍數。", AMBER),
    ]
    for index, (number, label, body, color) in enumerate(cards):
        x = 76 + index * 356
        card = QRectF(x, 305, 320, 445)
        rounded(p, card, QColor("#FFFDF9"), 24)
        p.setPen(QPen(QColor("#EAE3D7"), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(card, 24, 24)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawRoundedRect(QRectF(x + 28, 333, 48, 7), 3.5, 3.5)
        text(p, QRectF(x + 28, 405, 260, 98), number, size=71, color=INK, weight=QFont.Weight.Bold)
        text(p, QRectF(x + 28, 510, 260, 38), label, size=27, color=color, weight=QFont.Weight.DemiBold)
        text(p, QRectF(x + 28, 568, 258, 130), body, size=23, color=MUTED)
    text(p, QRectF(76, 830, 700, 48), "下一季的優先順序", size=36, weight=QFont.Weight.Bold)
    rows = [
        ("01", "把企業成功流程產品化", "讓續約洞察自動回到產品規劃。"),
        ("02", "擴展內容合作網絡", "建立可重複使用的聯合行銷機制。"),
        ("03", "守住交付品質", "把設計審查節點往前移，降低重工。"),
    ]
    for index, (num, title_value, body) in enumerate(rows):
        y = 900 + index * 150
        p.setPen(QPen(LINE, 1))
        p.drawLine(QPointF(76, y), QPointF(1114, y))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#E8F2EE"))
        p.drawEllipse(QPointF(110, y + 61), 27, 27)
        text(p, QRectF(91, y + 45, 38, 30), num, size=17, color=TEAL, weight=QFont.Weight.Bold, align=Qt.AlignmentFlag.AlignCenter)
        text(p, QRectF(158, y + 38, 500, 42), title_value, size=27, color=INK, weight=QFont.Weight.DemiBold)
        text(p, QRectF(158, y + 86, 800, 36), body, size=22, color=MUTED)


def draw_report_actions(p: QPainter) -> None:
    base_page(p, 4, 4, "下一步")
    text(p, QRectF(76, 155, 860, 72), "把洞察變成下季的行動。", size=60, weight=QFont.Weight.Bold)
    p.setPen(QPen(LINE, 1))
    p.drawLine(QPointF(76, 280), QPointF(1114, 280))
    columns = [
        ("01  /  產品", "企業成功流程", "把續約前 90 天的訊號整理成產品內的提醒，並與客戶成功團隊共用同一份健康分數。"),
        ("02  /  市場", "內容合作網絡", "先從三個垂直產業開始，建立固定節奏的共同內容與轉介機制，量測每一條合作的貢獻。"),
        ("03  /  營運", "交付品質前移", "在需求確認時就完成風險標記，每兩週檢視一次重工原因，讓設計與工程共享品質指標。"),
    ]
    for index, (eyebrow, title_value, body) in enumerate(columns):
        x = 76 + index * 356
        text(p, QRectF(x, 335, 300, 34), eyebrow, size=20, color=CORAL, weight=QFont.Weight.DemiBold)
        text(p, QRectF(x, 386, 300, 85), title_value, size=34, color=INK, weight=QFont.Weight.Bold)
        text(p, QRectF(x, 488, 298, 260), body, size=23, color=MUTED)
        rounded(p, QRectF(x, 780, 300, 4), QColor("#E3DBCC"), 2)
        w = 300 * (1 - index * 0.18)
        rounded(p, QRectF(x, 780, w, 4), TEAL if index == 0 else QColor("#B7CFC8"), 2)
    note = QRectF(76, 1010, 1038, 245)
    rounded(p, note, QColor("#EAF3EF"), 24)
    text(p, QRectF(112, 1052, 320, 40), "決策請求", size=24, color=TEAL_DARK, weight=QFont.Weight.DemiBold)
    text(
        p,
        QRectF(112, 1100, 930, 110),
        "核可下一季的企業成功流程專案，並讓內容合作預算延續兩個季度。\n預計在第 6 週回報第一批導入指標。",
        size=29,
        color=INK,
    )
    rounded(p, QRectF(76, 1345, 176, 54), TEAL, 27)
    text(p, QRectF(76, 1353, 176, 38), "核可此提案", size=22, color=QColor("#FFFFFF"), weight=QFont.Weight.DemiBold, align=Qt.AlignmentFlag.AlignHCenter)
    text(p, QRectF(276, 1352, 500, 40), "Owner · 策略與營運組", size=23, color=MUTED)


def draw_design_cover(p: QPainter) -> None:
    p.fillRect(QRectF(0, 0, W, H), QColor("#F5EDE5"))
    rounded(p, QRectF(0, 0, 468, H), CORAL, 0)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 34))
    p.drawEllipse(QPointF(250, 1320), 470, 470)
    p.setBrush(QColor(255, 255, 255, 28))
    p.drawEllipse(QPointF(400, 250), 240, 240)
    p.setFont(font(22, QFont.Weight.DemiBold))
    p.setPen(QColor("#FFF3EB"))
    p.drawText(QRectF(72, 72, 320, 32), Qt.AlignmentFlag.AlignLeft, "PROPOSAL  /  V2")
    text(p, QRectF(600, 255, 455, 58), "首頁改版提案", size=30, color=CORAL, weight=QFont.Weight.DemiBold)
    text(p, QRectF(598, 330, 525, 250), "讓進站的人\n更快找到價值。", size=68, color=INK, weight=QFont.Weight.Bold)
    text(
        p,
        QRectF(602, 685, 480, 150),
        "以更清楚的資訊層級，\n重新安排首頁的敘事與行動路徑。",
        size=27,
        color=MUTED,
    )
    p.setPen(QPen(CORAL, 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(72, 1150), QPointF(380, 1150))
    p.setFont(font(22))
    p.setPen(QColor("#FFF0E7"))
    text(p, QRectF(72, 1180, 320, 90), "NORTHWIND STUDIO\nDESIGN TEAM · 2026.10", size=22, color=QColor("#FFF0E7"))
    text(p, QRectF(600, 1390, 430, 40), "為 11 月的品牌發表準備", size=22, color=MUTED)


def draw_design_mockup(p: QPainter) -> None:
    base_page(p, 2, 3, "設計方向")
    text(p, QRectF(76, 150, 760, 66), "第一屏就是承諾。", size=58, weight=QFont.Weight.Bold)
    text(p, QRectF(76, 230, 750, 38), "用一個清楚的訊息，換取一次點擊。", size=26, color=MUTED)
    browser = QRectF(76, 320, 1038, 880)
    rounded(p, browser, QColor("#FFFDF9"), 22)
    p.setPen(QPen(QColor("#E4DCCD"), 1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(browser, 22, 22)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#F0EBE2"))
    p.drawRoundedRect(QRectF(76, 320, 1038, 62), 22, 22)
    p.setBrush(QColor("#FFFDF9"))
    p.drawRect(QRectF(76, 352, 1038, 30))
    for index, color in enumerate(("#DFA28F", "#EAC58A", "#A8C7BC")):
        p.setBrush(QColor(color))
        p.drawEllipse(QPointF(110 + index * 27, 351), 7, 7)
    p.setBrush(QColor("#E8E1D5"))
    p.drawRoundedRect(QRectF(215, 338, 430, 25), 12, 12)
    hero = QRectF(112, 415, 966, 430)
    gradient = QLinearGradient(hero.topLeft(), hero.topRight())
    gradient.setColorAt(0, QColor("#E8F1EC"))
    gradient.setColorAt(1, QColor("#F6E9DB"))
    rounded(p, hero, gradient, 16)
    text(p, QRectF(156, 476, 500, 190), "把好設計\n變成好生意。", size=64, color=INK, weight=QFont.Weight.Bold)
    text(p, QRectF(160, 676, 500, 60), "從品牌策略到數位體驗，一起把想法做對。", size=24, color=MUTED)
    rounded(p, QRectF(160, 758, 178, 50), CORAL, 25)
    text(p, QRectF(160, 766, 178, 32), "開始合作", size=21, color=QColor("#FFFFFF"), weight=QFont.Weight.DemiBold, align=Qt.AlignmentFlag.AlignHCenter)
    p.setPen(QPen(QColor("#D8CFC0"), 1))
    p.drawLine(QPointF(744, 450), QPointF(1036, 450))
    p.drawLine(QPointF(744, 450), QPointF(744, 800))
    rounded(p, QRectF(730, 450, 300, 250), QColor("#FFFFFF"), 14)
    text(p, QRectF(758, 478, 240, 38), "本季觀點", size=23, color=CORAL, weight=QFont.Weight.DemiBold)
    text(p, QRectF(758, 534, 240, 80), "品牌不是一次\n大改版。", size=32, color=INK, weight=QFont.Weight.Bold)
    text(p, QRectF(758, 630, 238, 50), "而是每一次互動的累積。", size=18, color=MUTED)
    for index in range(3):
        x = 112 + index * 330
        card = QRectF(x, 880, 300, 250)
        rounded(p, card, QColor("#F6F1E8"), 16)
        rounded(p, QRectF(x + 24, 910, 50, 8), [TEAL, CORAL, AMBER][index], 4)
        text(p, QRectF(x + 24, 942, 245, 39), ["清楚", "一致", "有記憶點"][index], size=27, color=INK, weight=QFont.Weight.Bold)
        text(
            p,
            QRectF(x + 24, 996, 245, 100),
            ["先說結論，再展開細節。", "跨裝置保持同一種語氣。", "讓一個畫面只說一件事。"][index],
            size=20,
            color=MUTED,
        )


def draw_design_cards(p: QPainter) -> None:
    base_page(p, 3, 3, "下一步")
    text(p, QRectF(76, 150, 760, 60), "三個設計原則，一個方向。", size=54, weight=QFont.Weight.Bold)
    principles = [
        ("01", "少一點，但更清楚", "首屏只保留一個主張與一個主要行動。", TEAL),
        ("02", "讓節奏有呼吸", "用留白與尺度，區分訊息的重要程度。", CORAL),
        ("03", "每個細節都可延伸", "模組化的版型，讓後續頁面快速長出來。", AMBER),
    ]
    for index, (num, title_value, body, color) in enumerate(principles):
        y = 300 + index * 270
        p.setPen(QPen(LINE, 1))
        p.drawLine(QPointF(76, y), QPointF(1114, y))
        text(p, QRectF(84, y + 52, 90, 60), num, size=37, color=color, weight=QFont.Weight.Bold)
        text(p, QRectF(190, y + 48, 450, 54), title_value, size=37, color=INK, weight=QFont.Weight.DemiBold)
        text(p, QRectF(680, y + 55, 420, 70), body, size=23, color=MUTED, align=Qt.AlignmentFlag.AlignRight)
    box = QRectF(76, 1200, 1038, 255)
    rounded(p, box, QColor("#E9F2ED"), 24)
    text(p, QRectF(116, 1242, 300, 42), "RECOMMENDATION", size=19, color=TEAL, weight=QFont.Weight.Bold)
    text(p, QRectF(116, 1292, 920, 100), "先以 A 方向進行兩週的可用性測試，再進入視覺細部。\n預計 11 月 8 日進行第一次評審。", size=27, color=INK)
    rounded(p, QRectF(76, 1510, 196, 50), TEAL, 25)
    text(p, QRectF(76, 1518, 196, 31), "排入下週議程", size=20, color=QColor("#FFFFFF"), weight=QFont.Weight.DemiBold, align=Qt.AlignmentFlag.AlignHCenter)


def draw_confidential_cover(p: QPainter) -> None:
    p.fillRect(QRectF(0, 0, W, H), QColor("#18312C"))
    p.setPen(QPen(QColor(255, 255, 255, 34), 1))
    for x in (76, 1114):
        p.drawLine(QPointF(x, 80), QPointF(x, H - 80))
    p.setFont(font(21, QFont.Weight.DemiBold))
    p.setPen(QColor("#F2A65A"))
    p.drawText(QRectF(120, 110, 500, 30), Qt.AlignmentFlag.AlignLeft, "CONFIDENTIAL / BOARD PACK")
    text(p, QRectF(118, 420, 900, 330), "董事會\n季度附件", size=120, color=QColor("#F7F4ED"), weight=QFont.Weight.Bold)
    p.setPen(QPen(QColor("#F2A65A"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(124, 800), QPointF(300, 800))
    text(p, QRectF(120, 850, 760, 100), "本文件包含尚未公開的營運資訊。\n請僅在指定會議中使用。", size=29, color=QColor("#B7C8C2"))
    rounded(p, QRectF(120, 1180, 230, 52), QColor("#F2A65A"), 26)
    text(p, QRectF(120, 1188, 230, 32), "限閱文件", size=20, color=QColor("#18312C"), weight=QFont.Weight.DemiBold, align=Qt.AlignmentFlag.AlignHCenter)
    text(p, QRectF(120, 1450, 600, 50), "2026.10  ·  第 04 季", size=23, color=QColor("#7F9991"))


def draw_confidential_table(p: QPainter) -> None:
    p.fillRect(QRectF(0, 0, W, H), QColor("#F8F5EE"))
    text(p, QRectF(76, 115, 900, 50), "附錄：客戶集中度", size=43, weight=QFont.Weight.Bold)
    text(p, QRectF(76, 180, 900, 35), "前五名客戶貢獻佔比，依合約金額計算。", size=22, color=MUTED)
    header = QRectF(76, 280, 1038, 68)
    rounded(p, header, QColor("#18312C"), 12)
    columns = [("客戶", 100), ("產業", 470), ("年約金額", 760), ("佔比", 950)]
    for label, x in columns:
        text(p, QRectF(x, 300, 210, 30), label, size=19, color=QColor("#F2A65A"), weight=QFont.Weight.DemiBold)
    rows = [
        ("Aurora Labs", "企業軟體", "NT$ 18.4M", "14.2%"),
        ("Harbor Group", "零售", "NT$ 14.1M", "10.9%"),
        ("Mori Health", "醫療", "NT$ 11.8M", "9.1%"),
        ("Field Notes", "媒體", "NT$ 9.6M", "7.4%"),
        ("Beacon Air", "物流", "NT$ 8.2M", "6.3%"),
    ]
    for index, row in enumerate(rows):
        y = 348 + index * 106
        if index % 2 == 0:
            rounded(p, QRectF(76, y, 1038, 106), QColor("#FDFBF7"), 10)
        p.setPen(QPen(QColor("#EDE6DA"), 1))
        p.drawLine(QPointF(76, y + 106), QPointF(1114, y + 106))
        for value, (_, x) in zip(row, columns):
            text(p, QRectF(x, y + 35, 300, 40), value, size=25, color=INK if x < 900 else TEAL_DARK, weight=QFont.Weight.DemiBold if x >= 900 else QFont.Weight.Normal)
    rounded(p, QRectF(76, 980, 1038, 180), QColor("#F3EADD"), 18)
    text(p, QRectF(110, 1016, 950, 45), "觀察", size=22, color=CORAL, weight=QFont.Weight.DemiBold)
    text(p, QRectF(110, 1060, 940, 80), "前五名客戶合計佔比 47.9%，較上季下降 2.4 個百分點；\n單一客戶集中度仍低於董事會設定之上限。", size=26, color=INK)


def _write_page(path: Path, draw) -> None:
    writer = QPdfWriter(str(path))
    writer.setPageSize(QPageSize(QPageSize.A4))
    writer.setResolution(144)
    painter = QPainter(writer)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    draw(painter)
    painter.end()
    del painter, writer
    gc.collect()


def make_document(output: Path, draws: list, title: str, password: str | None = None) -> None:
    with tempfile.TemporaryDirectory(prefix="pdf-samples-") as temp:
        page_paths = []
        for index, draw in enumerate(draws):
            page_path = Path(temp) / f"page-{index}.pdf"
            _write_page(page_path, draw)
            page_paths.append(page_path)
        writer = PdfWriter()
        for page_path in page_paths:
            reader = PdfReader(str(page_path))
            writer.add_page(reader.pages[0])
        writer.add_metadata({"/Title": title, "/Author": "Northwind Studio"})
        if password:
            writer.encrypt(password, owner_password="owner-2026")
        with open(output, "wb") as stream:
            writer.write(stream)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("PDF 併頁器範例產生器")
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "samples"
    output.mkdir(parents=True, exist_ok=True)
    make_document(
        output / "季度營運報告.pdf",
        [draw_report_cover, draw_report_chart, draw_report_metrics, draw_report_actions],
        "2026 第四季營運回顧",
    )
    make_document(
        output / "設計提案_首頁改版.pdf",
        [draw_design_cover, draw_design_mockup, draw_design_cards],
        "首頁改版提案",
    )
    make_document(
        output / "機密_董事會附件.pdf",
        [draw_confidential_cover, draw_confidential_table],
        "董事會季度附件",
        password="open123",
    )
    for path in sorted(output.glob("*.pdf")):
        reader = PdfReader(str(path))
        suffix = ""
        if reader.is_encrypted:
            suffix = "（已加密）"
            reader.decrypt("open123")
        print(f"{path.name}: {len(reader.pages)} 頁{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
