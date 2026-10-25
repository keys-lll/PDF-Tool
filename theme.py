"""Application-wide Qt stylesheet."""

APP_STYLE = """
QWidget {
    font-family: "Noto Sans CJK TC";
    font-size: 10pt;
    color: #293832;
}
QMainWindow, QWidget#root, QWidget#contentPanel {
    background: #F5F2EB;
}
QMenuBar {
    background: #FBFAF7;
    color: #2D3D37;
    border-bottom: 1px solid #E8E1D5;
    padding: 2px 8px;
}
QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
    border-radius: 5px;
}
QMenuBar::item:selected {
    background: #EFEAE0;
}
QMenu {
    background: #FFFDF9;
    border: 1px solid #DED6C8;
    border-radius: 7px;
    padding: 5px;
}
QMenu::item {
    padding: 7px 28px 7px 22px;
    border-radius: 5px;
}
QMenu::item:selected {
    background: #E7F1ED;
    color: #115E59;
}
QMenu::separator {
    height: 1px;
    background: #ECE5D9;
    margin: 5px 8px;
}
QStatusBar {
    background: #FBFAF7;
    color: #7B827B;
    border-top: 1px solid #E8E1D5;
    font-size: 9pt;
    padding-left: 8px;
}
QStatusBar::item {
    border: none;
}

QFrame#sidebar {
    background: #FBFAF7;
    border-right: 1px solid #E7E0D4;
}
QLabel#brandTitle {
    font-size: 17pt;
    font-weight: 700;
    color: #173A32;
}
QLabel#brandSubtitle {
    font-size: 8.8pt;
    color: #889087;
}
QLabel#sectionTitle {
    font-size: 10pt;
    font-weight: 600;
    color: #35443E;
}
QLabel#countChip {
    background: #EFEBE2;
    color: #747B73;
    border-radius: 9px;
    padding: 3px 9px;
    font-size: 8.3pt;
}
QLabel#sideHint {
    color: #989084;
    font-size: 8.5pt;
}
QFrame#sourceRow {
    background: #FFFFFF;
    border: 1px solid #E9E2D7;
    border-radius: 10px;
}
QFrame#sourceRow:hover {
    border-color: #CFDCD7;
    background: #FDFEFC;
}
QFrame#sourceRow[tone="locked"] {
    background: #FFFCF5;
    border-color: #EFD5AF;
}
QFrame#sourceRow[tone="error"] {
    background: #FFFBF9;
    border-color: #F0C8C3;
}
QLabel#sourceName {
    color: #263A34;
    font-size: 9pt;
    font-weight: 600;
}
QLabel#sourceMeta {
    color: #8B8F86;
    font-size: 8.2pt;
}
QLabel#sourceMeta[tone="ready"] {
    color: #4E7C70;
}
QLabel#sourceMeta[tone="locked"] {
    color: #A96313;
}
QLabel#sourceMeta[tone="error"] {
    color: #B42318;
}
QPushButton#unlockButton {
    background: #FFF9EF;
    color: #9B5B13;
    border: 1px solid #E5C691;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 8.2pt;
    font-weight: 600;
}
QPushButton#unlockButton:hover {
    background: #FFF2DD;
    border-color: #D9B16F;
}
QPushButton#unlockButton:pressed {
    background: #F7E7CB;
}
QPushButton#removeSourceButton {
    background: transparent;
    color: #A59B8D;
    border: none;
    border-radius: 6px;
    font-size: 13pt;
    padding: 0;
}
QPushButton#removeSourceButton:hover {
    background: #FBEDEA;
    color: #B42318;
}
QLabel#sourceEmpty {
    color: #9B9387;
    font-size: 9pt;
    background: #F7F4ED;
    border: 1px dashed #DDD5C7;
    border-radius: 9px;
    padding: 16px 14px;
}
QFrame#securityCard {
    background: #F3F0E9;
    border: 1px solid #E7E1D5;
    border-radius: 9px;
}
QLabel#securityTitle {
    color: #5F6C66;
    font-size: 8.5pt;
    font-weight: 600;
}
QLabel#securityBody {
    color: #90968E;
    font-size: 8pt;
}
QFrame#rule {
    background: #E9E2D6;
    border: none;
    max-height: 1px;
    min-height: 1px;
}

QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QScrollBar:vertical {
    background: transparent;
    width: 11px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #D5CEC1;
    min-height: 32px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background: #BFB6A7;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    background: transparent;
    height: 11px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #D5CEC1;
    min-width: 32px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

QPushButton {
    outline: none;
}
QPushButton#primaryButton {
    background: #0F766E;
    color: #FFFFFF;
    border: 2px solid transparent;
    border-radius: 9px;
    padding: 9px 18px;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background: #0D8A7E;
}
QPushButton#primaryButton:pressed {
    background: #0B5F58;
}
QPushButton#primaryButton:focus {
    border: 2px solid #8FE2D6;
}
QPushButton#primaryButton:disabled {
    background: #C9D8D4;
    color: #F4F8F7;
}
QPushButton#secondaryButton {
    background: #FFFDF9;
    color: #40534C;
    border: 1px solid #D9D2C6;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton#secondaryButton:hover {
    background: #F7F4ED;
    border-color: #C8BFB0;
}
QPushButton#secondaryButton:pressed {
    background: #EFEBE1;
}
QPushButton#secondaryButton:focus {
    border: 1px solid #0F766E;
}
QPushButton#ghostButton {
    background: transparent;
    color: #5C6B64;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 9pt;
}
QPushButton#ghostButton:hover {
    background: #ECE8DF;
    color: #2E423B;
}
QPushButton#ghostButton:pressed {
    background: #E4DED4;
}
QPushButton#ghostButton:disabled {
    color: #B8B2A7;
    background: transparent;
}

QLabel#pageTitle {
    font-size: 23pt;
    font-weight: 700;
    color: #183A32;
}
QLabel#pageSubtitle {
    color: #7D847D;
    font-size: 9.5pt;
}
QLabel#pageHint {
    color: #928A7E;
    font-size: 8.8pt;
}
QLabel#noticeLabel {
    background: #FFF7E8;
    color: #89550F;
    border: 1px solid #EFD3A0;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 9pt;
}
QLabel#emptyEyebrow {
    color: #0F766E;
    font-size: 8.3pt;
    font-weight: 700;
}
QLabel#emptyTitle {
    color: #1E3A33;
    font-size: 20pt;
    font-weight: 700;
}
QLabel#emptyBody {
    color: #7E867F;
    font-size: 9.5pt;
}
QListView#pageList {
    background: transparent;
    border: none;
    outline: none;
}
QListView#pageList::item {
    background: transparent;
    border: none;
}

QDialog {
    background: #FBFAF7;
}
QLabel#dialogTitle {
    font-size: 15pt;
    font-weight: 700;
    color: #203C35;
}
QLabel#dialogFileName {
    background: #F2EEE5;
    color: #52615B;
    border-radius: 7px;
    padding: 8px 12px;
    font-size: 9pt;
}
QLabel#dialogBody {
    color: #7B827A;
    font-size: 9pt;
}
QLabel#dialogError {
    background: #FEF3F2;
    color: #B42318;
    border: 1px solid #F3C9C5;
    border-radius: 7px;
    padding: 7px 10px;
    font-size: 8.8pt;
}
QLineEdit {
    background: #FFFFFF;
    color: #263A34;
    border: 1px solid #D8D0C3;
    border-radius: 8px;
    padding: 9px 11px;
    selection-background-color: #0F766E;
    selection-color: #FFFFFF;
}
QLineEdit:focus {
    border: 1px solid #0F766E;
}
QLineEdit:disabled {
    background: #F3F0E9;
}
QCheckBox {
    color: #65726C;
    font-size: 8.8pt;
    spacing: 6px;
}
QDialogButtonBox QPushButton {
    min-width: 84px;
}

QProgressDialog {
    background: #FBFAF7;
}
QProgressDialog QLabel {
    color: #35443E;
}
QProgressBar {
    background: #E8E2D7;
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: #0F766E;
    border-radius: 5px;
}
QProgressDialog QPushButton {
    background: #FFFDF9;
    color: #40534C;
    border: 1px solid #D9D2C6;
    border-radius: 7px;
    padding: 6px 14px;
    min-width: 66px;
}
QProgressDialog QPushButton:hover {
    background: #F6F3EC;
}
QMessageBox {
    background: #FBFAF7;
}
QMessageBox QLabel {
    color: #2A3834;
    font-size: 9.5pt;
}
QMessageBox QPushButton {
    background: #FFFDF9;
    color: #40534C;
    border: 1px solid #D9D2C6;
    border-radius: 7px;
    padding: 7px 15px;
    min-width: 72px;
}
QMessageBox QPushButton:hover {
    background: #F6F3EC;
}
QMessageBox QPushButton:default {
    background: #0F766E;
    color: #FFFFFF;
    border-color: #0F766E;
}
QToolTip {
    background: #243A33;
    color: #FFFFFF;
    border: none;
    padding: 5px 8px;
    font-size: 8.5pt;
}
"""


def build_stylesheet(font_family: str) -> str:
    """Return the app stylesheet using the platform's preferred UI font."""
    return APP_STYLE.replace('"Noto Sans CJK TC"', f'"{font_family}"')
