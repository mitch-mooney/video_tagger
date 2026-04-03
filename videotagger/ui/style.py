# videotagger/ui/style.py
"""
Global dark-sports stylesheet.
Palette drawn from the Cheap Stats logo: deep navy background, teal (#00b09b) accent.
"""

APP_STYLESHEET = """
/* ── Base ──────────────────────────────────────────────── */
QMainWindow, QWidget {
    background: #0d1117;
    color: #dde3ea;
    font-family: "Segoe UI", sans-serif;
    font-size: 9pt;
}

/* ── Menu bar ───────────────────────────────────────────── */
QMenuBar {
    background: #090d12;
    color: #dde3ea;
    border-bottom: 1px solid #1e2a38;
    padding: 2px 4px;
}
QMenuBar::item { padding: 4px 10px; border-radius: 3px; }
QMenuBar::item:selected { background: #00b09b; color: #ffffff; }

QMenu {
    background: #13191f;
    border: 1px solid #1e2a38;
    color: #dde3ea;
    padding: 4px 0;
}
QMenu::item { padding: 5px 24px 5px 12px; }
QMenu::item:selected { background: #00b09b; color: #ffffff; }
QMenu::separator { height: 1px; background: #1e2a38; margin: 4px 0; }

/* ── Splitter ────────────────────────────────────────────── */
QSplitter::handle { background: #1e2a38; }
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical   { height: 2px; }

/* ── Tab widget ──────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #1e2a38;
    background: #0d1117;
    top: -1px;
}
QTabBar::tab {
    background: #090d12;
    color: #7d8fa3;
    padding: 6px 18px;
    border: 1px solid #1e2a38;
    border-bottom: none;
    font-weight: 600;
    letter-spacing: 0.4px;
    min-width: 60px;
}
QTabBar::tab:selected {
    background: #0d1117;
    color: #00b09b;
    border-top: 2px solid #00b09b;
}
QTabBar::tab:hover:!selected { background: #13191f; color: #dde3ea; }

/* ── Tree widget (Tags) ──────────────────────────────────── */
QTreeWidget {
    background: #0d1117;
    border: 1px solid #1e2a38;
    outline: none;
    show-decoration-selected: 1;
}
QTreeWidget::item { padding: 4px 2px; }
QTreeWidget::item:hover { background: #1a2b3c; }
QTreeWidget::item:selected { background: #003d4f; color: #00b09b; }
QTreeWidget::branch:has-children:closed { image: none; }
QTreeWidget::branch:has-children:open   { image: none; }

/* ── Table widget (Clips) ────────────────────────────────── */
QTableWidget {
    background: #0d1117;
    border: 1px solid #1e2a38;
    gridline-color: #1a2434;
    outline: none;
    alternate-background-color: #0f1620;
}
QTableWidget::item { padding: 4px 8px; }
QTableWidget::item:selected { background: #003d4f; color: #dde3ea; }

QHeaderView::section {
    background: #090d12;
    color: #7d8fa3;
    border: none;
    border-right: 1px solid #1e2a38;
    border-bottom: 1px solid #1e2a38;
    padding: 5px 8px;
    font-weight: 700;
    font-size: 8pt;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
QHeaderView::section:last { border-right: none; }

/* ── List widget (Playlists) ─────────────────────────────── */
QListWidget {
    background: #0d1117;
    border: 1px solid #1e2a38;
    outline: none;
}
QListWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #1a2434;
}
QListWidget::item:hover { background: #1a2b3c; }
QListWidget::item:selected { background: #003d4f; color: #00b09b; }

/* ── Buttons ─────────────────────────────────────────────── */
QPushButton {
    background: #13191f;
    color: #dde3ea;
    border: 1px solid #1e2a38;
    border-radius: 4px;
    padding: 5px 14px;
    font-weight: 600;
    min-width: 28px;
}
QPushButton:hover { background: #1a2b3c; border-color: #00b09b; color: #00b09b; }
QPushButton:pressed { background: #003d4f; }
QPushButton:disabled { color: #3d4f5e; border-color: #1a2434; }

/* ── Slider ──────────────────────────────────────────────── */
QSlider::groove:horizontal {
    background: #1e2a38;
    height: 4px;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #00b09b;
    height: 4px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #00b09b;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}
QSlider::handle:horizontal:hover { background: #00d4b8; }

/* ── Status bar ──────────────────────────────────────────── */
QStatusBar {
    background: #090d12;
    color: #7d8fa3;
    border-top: 1px solid #1e2a38;
    font-size: 8pt;
}

/* ── Line edit ───────────────────────────────────────────── */
QLineEdit {
    background: #090d12;
    border: 1px solid #1e2a38;
    border-radius: 4px;
    color: #dde3ea;
    padding: 5px 8px;
    selection-background-color: #003d4f;
}
QLineEdit:focus { border-color: #00b09b; }

/* ── Combo box ───────────────────────────────────────────── */
QComboBox {
    background: #090d12;
    border: 1px solid #1e2a38;
    border-radius: 4px;
    color: #dde3ea;
    padding: 5px 8px;
    min-width: 80px;
}
QComboBox:focus { border-color: #00b09b; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #13191f;
    border: 1px solid #1e2a38;
    color: #dde3ea;
    selection-background-color: #003d4f;
    outline: none;
}

/* ── Spin boxes ──────────────────────────────────────────── */
QDoubleSpinBox, QSpinBox {
    background: #090d12;
    border: 1px solid #1e2a38;
    border-radius: 4px;
    color: #dde3ea;
    padding: 4px 8px;
}
QDoubleSpinBox:focus, QSpinBox:focus { border-color: #00b09b; }
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {
    background: #13191f;
    border: none;
    width: 16px;
}

/* ── Scroll bars ─────────────────────────────────────────── */
QScrollBar:vertical {
    background: #090d12; width: 8px; border: none; margin: 0;
}
QScrollBar::handle:vertical {
    background: #1e2a38; border-radius: 4px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #00b09b; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #090d12; height: 8px; border: none; margin: 0;
}
QScrollBar::handle:horizontal {
    background: #1e2a38; border-radius: 4px; min-width: 24px;
}
QScrollBar::handle:horizontal:hover { background: #00b09b; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Text / plain edit (Help panel) ─────────────────────── */
QTextBrowser {
    background: #090d12;
    border: 1px solid #1e2a38;
    color: #dde3ea;
    selection-background-color: #003d4f;
    font-size: 9pt;
    line-height: 1.6;
}

/* ── Dialogs ─────────────────────────────────────────────── */
QDialog {
    background: #0d1117;
}
QDialogButtonBox QPushButton { min-width: 72px; }

/* ── Labels ──────────────────────────────────────────────── */
QLabel { color: #dde3ea; background: transparent; }

/* ── Tooltip ─────────────────────────────────────────────── */
QToolTip {
    background: #13191f;
    border: 1px solid #00b09b;
    color: #dde3ea;
    padding: 4px 8px;
    border-radius: 3px;
}

/* ── Progress dialog ─────────────────────────────────────── */
QProgressDialog { background: #0d1117; }
QProgressBar {
    background: #090d12;
    border: 1px solid #1e2a38;
    border-radius: 4px;
    text-align: center;
    color: #dde3ea;
}
QProgressBar::chunk {
    background: #00b09b;
    border-radius: 3px;
}

/* ── Message box ─────────────────────────────────────────── */
QMessageBox { background: #0d1117; }
QMessageBox QLabel { color: #dde3ea; }
"""
