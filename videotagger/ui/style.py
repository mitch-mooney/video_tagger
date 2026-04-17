# videotagger/ui/style.py
"""
VideoTagger v2.0 — Studio Dark theme.
Deep void blacks, precise surface hierarchy, underline tab navigation.
Call build_stylesheet(accent) to apply a custom team accent color.
"""

_DEFAULT_ACCENT = "#00b09b"
_DEFAULT_DARK   = "#003d4f"   # 30% accent
_DEFAULT_LIGHT  = "#00d4b8"   # 120% accent

_TEMPLATE = """
/* ── Reset & Base ────────────────────────────────────────────── */
QMainWindow, QWidget {
    background: #080c12;
    color: #d8e4ef;
    font-family: "Segoe UI Variable Text", "Segoe UI", "SF Pro Text", system-ui, sans-serif;
    font-size: 9pt;
}

/* ── Menu bar ─────────────────────────────────────────────────── */
QMenuBar {
    background: #060911;
    color: #c0cedd;
    border-bottom: 1px solid #141e2e;
    padding: 1px 4px;
    spacing: 2px;
}
QMenuBar::item {
    padding: 4px 12px;
    border-radius: 4px;
    background: transparent;
}
QMenuBar::item:selected { background: #00b09b; color: #fff; }

QMenu {
    background: #0e1623;
    border: 1px solid #1c2a3e;
    color: #d8e4ef;
    padding: 5px 0;
    border-radius: 6px;
}
QMenu::item { padding: 6px 28px 6px 14px; }
QMenu::item:selected { background: #00b09b; color: #fff; border-radius: 3px; }
QMenu::separator { height: 1px; background: #1c2a3e; margin: 4px 8px; }

/* ── Splitter ─────────────────────────────────────────────────── */
QSplitter::handle { background: #111826; }
QSplitter::handle:horizontal { width: 3px; }
QSplitter::handle:horizontal:hover { background: #00b09b; }
QSplitter::handle:vertical { height: 3px; }
QSplitter::handle:vertical:hover { background: #00b09b; }

/* ── Tab widget ───────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    border-top: 1px solid #141e2e;
    background: #080c12;
    top: 0px;
}
QTabBar {
    background: #060911;
    border-bottom: 1px solid #141e2e;
}
QTabBar::tab {
    background: transparent;
    color: #5a7490;
    padding: 8px 22px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    font-size: 8pt;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    min-width: 64px;
}
QTabBar::tab:selected {
    color: #00b09b;
    border-bottom: 2px solid #00b09b;
    background: transparent;
}
QTabBar::tab:hover:!selected {
    color: #c0cedd;
    border-bottom: 2px solid #1c2a3e;
    background: rgba(255,255,255,0.02);
}

/* ── Tree widget ──────────────────────────────────────────────── */
QTreeWidget {
    background: #080c12;
    border: 1px solid #141e2e;
    outline: none;
    show-decoration-selected: 1;
}
QTreeWidget::item { padding: 5px 4px; }
QTreeWidget::item:hover { background: #0f1826; }
QTreeWidget::item:selected {
    background: #0d2030;
    color: #00b09b;
    border-left: 2px solid #00b09b;
}
QTreeWidget::branch { background: #080c12; }

/* ── Table widget ─────────────────────────────────────────────── */
QTableWidget {
    background: #080c12;
    border: 1px solid #141e2e;
    gridline-color: #0e1622;
    outline: none;
    alternate-background-color: #0b1018;
    selection-background-color: #0d2030;
}
QTableWidget::item {
    padding: 5px 10px;
    border-bottom: 1px solid #0e1622;
}
QTableWidget::item:hover { background: #0f1826; }
QTableWidget::item:selected {
    background: #0d2030;
    color: #d8e4ef;
}

QHeaderView {
    background: #060911;
    border: none;
}
QHeaderView::section {
    background: #060911;
    color: #4d6880;
    border: none;
    border-right: 1px solid #141e2e;
    border-bottom: 1px solid #141e2e;
    padding: 6px 10px;
    font-weight: 700;
    font-size: 7.5pt;
    letter-spacing: 1px;
    text-transform: uppercase;
}
QHeaderView::section:last { border-right: none; }
QHeaderView::section:hover { color: #c0cedd; background: #0b1018; }

/* ── List widget ──────────────────────────────────────────────── */
QListWidget {
    background: #080c12;
    border: 1px solid #141e2e;
    outline: none;
}
QListWidget::item {
    padding: 9px 12px;
    border-bottom: 1px solid #0e1622;
}
QListWidget::item:hover { background: #0f1826; }
QListWidget::item:selected {
    background: #0d2030;
    color: #00b09b;
}

/* ── Buttons ──────────────────────────────────────────────────── */
QPushButton {
    background: #0e1522;
    color: #c8d8e8;
    border: 1px solid #1a2840;
    border-radius: 5px;
    padding: 5px 16px;
    font-weight: 600;
    font-size: 9pt;
    min-width: 32px;
}
QPushButton:hover {
    background: #122030;
    border-color: #00b09b;
    color: #00b09b;
}
QPushButton:pressed {
    background: #0a1820;
    border-color: #003d4f;
    color: #00d4b8;
}
QPushButton:disabled {
    color: #283848;
    border-color: #111c28;
    background: #080c12;
}
QPushButton:default {
    border-color: #00b09b;
}

/* ── Slider ───────────────────────────────────────────────────── */
QSlider::groove:horizontal {
    background: #141e2e;
    height: 3px;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #00b09b;
    height: 3px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #fff;
    border: 2px solid #00b09b;
    width: 11px;
    height: 11px;
    margin: -4px 0;
    border-radius: 6px;
}
QSlider::handle:horizontal:hover {
    background: #00b09b;
    border-color: #00d4b8;
}

/* ── Line edit ────────────────────────────────────────────────── */
QLineEdit {
    background: #060911;
    border: 1px solid #1a2840;
    border-radius: 5px;
    color: #d8e4ef;
    padding: 6px 10px;
    selection-background-color: #003d4f;
    selection-color: #00d4b8;
}
QLineEdit:hover { border-color: #243a58; }
QLineEdit:focus { border-color: #00b09b; background: #080e18; }
QLineEdit:disabled { color: #283848; background: #080c12; }

/* ── Combo box ────────────────────────────────────────────────── */
QComboBox {
    background: #060911;
    border: 1px solid #1a2840;
    border-radius: 5px;
    color: #d8e4ef;
    padding: 6px 10px;
    min-width: 80px;
}
QComboBox:hover { border-color: #243a58; }
QComboBox:focus { border-color: #00b09b; }
QComboBox::drop-down {
    border: none;
    width: 24px;
    padding-right: 6px;
}
QComboBox QAbstractItemView {
    background: #0e1623;
    border: 1px solid #1c2a3e;
    color: #d8e4ef;
    selection-background-color: #0d2030;
    selection-color: #00b09b;
    outline: none;
    padding: 4px 0;
}

/* ── Spin boxes ───────────────────────────────────────────────── */
QDoubleSpinBox, QSpinBox {
    background: #060911;
    border: 1px solid #1a2840;
    border-radius: 5px;
    color: #d8e4ef;
    padding: 5px 8px;
}
QDoubleSpinBox:focus, QSpinBox:focus { border-color: #00b09b; }
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {
    background: #0e1522;
    border: none;
    width: 18px;
    border-radius: 2px;
}
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover,
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #122030;
}

/* ── Scrollbars ───────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 7px;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #1a2840;
    border-radius: 3px;
    min-height: 28px;
    margin: 1px;
}
QScrollBar::handle:vertical:hover { background: #00b09b; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QScrollBar:horizontal {
    background: transparent;
    height: 7px;
    border: none;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #1a2840;
    border-radius: 3px;
    min-width: 28px;
    margin: 1px;
}
QScrollBar::handle:horizontal:hover { background: #00b09b; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

/* ── Status bar ───────────────────────────────────────────────── */
QStatusBar {
    background: #060911;
    color: #4d6880;
    border-top: 1px solid #141e2e;
    font-size: 8pt;
    padding: 0 4px;
}

/* ── Text browser ─────────────────────────────────────────────── */
QTextBrowser {
    background: #060911;
    border: 1px solid #141e2e;
    color: #d8e4ef;
    selection-background-color: #003d4f;
    font-size: 9pt;
}

/* ── Check box ────────────────────────────────────────────────── */
QCheckBox { spacing: 8px; color: #c0cedd; }
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid #1a2840;
    border-radius: 3px;
    background: #060911;
}
QCheckBox::indicator:hover { border-color: #00b09b; }
QCheckBox::indicator:checked {
    background: #00b09b;
    border-color: #00b09b;
    image: none;
}
QCheckBox::indicator:checked:hover { background: #00d4b8; }

/* ── Group box ────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #1a2840;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: 600;
    font-size: 8.5pt;
    color: #7a9ab8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    background: #080c12;
    color: #7a9ab8;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    font-size: 7.5pt;
}

/* ── Dialogs ──────────────────────────────────────────────────── */
QDialog { background: #080c12; }
QDialogButtonBox QPushButton { min-width: 80px; }

/* ── Labels ───────────────────────────────────────────────────── */
QLabel { color: #d8e4ef; background: transparent; }

/* ── Tooltip ──────────────────────────────────────────────────── */
QToolTip {
    background: #0e1623;
    border: 1px solid #00b09b;
    color: #d8e4ef;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 8.5pt;
}

/* ── Progress ─────────────────────────────────────────────────── */
QProgressDialog { background: #080c12; }
QProgressBar {
    background: #060911;
    border: 1px solid #1a2840;
    border-radius: 4px;
    text-align: center;
    color: #d8e4ef;
    font-size: 8pt;
    height: 6px;
}
QProgressBar::chunk {
    background: #00b09b;
    border-radius: 3px;
}

/* ── Message box ──────────────────────────────────────────────── */
QMessageBox { background: #080c12; }
QMessageBox QLabel { color: #d8e4ef; }
"""


def build_stylesheet(accent: str = _DEFAULT_ACCENT) -> str:
    """Return the app stylesheet with accent replaced by the given hex color."""
    from PyQt6.QtGui import QColor
    c = QColor(accent)
    r, g, b = c.red(), c.green(), c.blue()
    dark_r, dark_g, dark_b = int(r * 0.3), int(g * 0.3), int(b * 0.3)
    light_r = min(255, int(r * 1.2))
    light_g = min(255, int(g * 1.2))
    light_b = min(255, int(b * 1.2))
    accent_dark  = f"#{dark_r:02x}{dark_g:02x}{dark_b:02x}"
    accent_light = f"#{light_r:02x}{light_g:02x}{light_b:02x}"
    return (
        _TEMPLATE
        .replace(_DEFAULT_LIGHT, accent_light)
        .replace(_DEFAULT_DARK,  accent_dark)
        .replace(_DEFAULT_ACCENT, accent)
    )


APP_STYLESHEET = build_stylesheet()
