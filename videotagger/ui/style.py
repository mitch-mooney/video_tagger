# videotagger/ui/style.py
"""
VideoTagger — Broadcast Studio theme.

Refined dark with three surface elevations, a signature electric-teal accent, an
amber marking signal, condensed display headers, visible focus rings, and a unified
spacing/radius scale. Colours and fonts come from ``theme.py``.

Call ``build_stylesheet(accent)`` to apply a custom team accent colour.
"""
from videotagger.ui import theme


def _build(accent: str, accent_dim: str, accent_light: str) -> str:
    t = theme
    return f"""
/* ── Reset & Base ────────────────────────────────────────────── */
QMainWindow, QWidget {{
    background: {t.INK};
    color: {t.TEXT};
    font-family: {t.FONT_BODY};
    font-size: 9pt;
}}

/* ── Menu bar ─────────────────────────────────────────────────── */
QMenuBar {{
    background: {t.INK_DEEP};
    color: {t.MUTED};
    border-bottom: 1px solid {t.LINE};
    padding: 2px 6px;
    spacing: 2px;
}}
QMenuBar::item {{
    padding: 5px 12px;
    border-radius: 5px;
    background: transparent;
}}
QMenuBar::item:selected {{ background: {accent_dim}; color: {t.TEXT}; }}

QMenu {{
    background: {t.SURFACE_2};
    border: 1px solid {t.LINE};
    color: {t.TEXT};
    padding: 6px 0;
    border-radius: 8px;
}}
QMenu::item {{ padding: 7px 28px 7px 16px; }}
QMenu::item:selected {{ background: {accent_dim}; color: {t.TEXT}; border-radius: 4px; }}
QMenu::separator {{ height: 1px; background: {t.LINE}; margin: 5px 10px; }}

/* ── Splitter ─────────────────────────────────────────────────── */
QSplitter::handle {{ background: {t.INK_DEEP}; }}
QSplitter::handle:horizontal {{ width: 4px; }}
QSplitter::handle:horizontal:hover {{ background: {accent}; }}
QSplitter::handle:vertical {{ height: 4px; }}
QSplitter::handle:vertical:hover {{ background: {accent}; }}

/* ── Tab widget ───────────────────────────────────────────────── */
QTabWidget::pane {{
    border: none;
    border-top: 1px solid {t.LINE};
    background: {t.SURFACE};
    top: 0px;
}}
QTabBar {{
    background: {t.INK_DEEP};
    border-bottom: 1px solid {t.LINE};
}}
QTabBar::tab {{
    background: transparent;
    color: {t.FAINT};
    padding: 10px 22px;
    border: none;
    border-bottom: 2px solid transparent;
    font-family: {t.FONT_DISPLAY};
    font-weight: 600;
    font-size: 8.5pt;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    min-width: 64px;
}}
QTabBar::tab:selected {{
    color: {accent};
    border-bottom: 2px solid {accent};
    background: transparent;
}}
QTabBar::tab:hover:!selected {{
    color: {t.MUTED};
    border-bottom: 2px solid {t.LINE};
    background: rgba(255,255,255,0.02);
}}

/* ── Tree widget ──────────────────────────────────────────────── */
QTreeWidget {{
    background: {t.SURFACE};
    border: 1px solid {t.LINE};
    border-radius: 8px;
    outline: none;
    show-decoration-selected: 1;
}}
QTreeWidget::item {{ padding: 6px 4px; border-radius: 5px; }}
QTreeWidget::item:hover {{ background: {t.SURFACE_2}; }}
QTreeWidget::item:selected {{
    background: {t.shade(accent_dim, 0.6)};
    color: {accent};
}}
QTreeWidget::branch {{ background: {t.SURFACE}; }}

/* ── Table widget ─────────────────────────────────────────────── */
QTableWidget {{
    background: {t.SURFACE};
    border: 1px solid {t.LINE};
    gridline-color: {t.LINE_SOFT};
    outline: none;
    alternate-background-color: {t.shade(t.SURFACE, 1.08)};
    selection-background-color: {t.shade(accent_dim, 0.55)};
}}
QTableWidget::item {{
    padding: 7px 12px;
    border-bottom: 1px solid {t.LINE_SOFT};
}}
QTableWidget::item:hover {{ background: {t.SURFACE_2}; }}
QTableWidget::item:selected {{
    background: {t.shade(accent_dim, 0.5)};
    color: {t.TEXT};
}}

QHeaderView {{ background: {t.INK_DEEP}; border: none; }}
QHeaderView::section {{
    background: {t.INK_DEEP};
    color: {t.FAINT};
    border: none;
    border-right: 1px solid {t.LINE};
    border-bottom: 1px solid {t.LINE};
    padding: 8px 12px;
    font-family: {t.FONT_DISPLAY};
    font-weight: 600;
    font-size: 8pt;
    letter-spacing: 1.4px;
    text-transform: uppercase;
}}
QHeaderView::section:last {{ border-right: none; }}
QHeaderView::section:hover {{ color: {t.MUTED}; background: {t.SURFACE}; }}

/* ── List widget ──────────────────────────────────────────────── */
QListWidget {{
    background: {t.SURFACE};
    border: 1px solid {t.LINE};
    border-radius: 8px;
    outline: none;
}}
QListWidget::item {{
    padding: 10px 12px;
    border-bottom: 1px solid {t.LINE_SOFT};
}}
QListWidget::item:hover {{ background: {t.SURFACE_2}; }}
QListWidget::item:selected {{
    background: {t.shade(accent_dim, 0.55)};
    color: {accent};
}}

/* ── Buttons ──────────────────────────────────────────────────── */
QPushButton {{
    background: {t.SURFACE_2};
    color: {t.TEXT};
    border: 1px solid {t.LINE};
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 600;
    font-size: 9pt;
    min-width: 32px;
}}
QPushButton:hover {{
    background: {t.shade(t.SURFACE_2, 1.18)};
    border-color: {accent};
    color: {accent};
}}
QPushButton:pressed {{
    background: {t.INK};
    border-color: {accent_dim};
    color: {accent_light};
}}
QPushButton:disabled {{
    color: {t.shade(t.FAINT, 0.7)};
    border-color: {t.LINE_SOFT};
    background: {t.INK};
}}
QPushButton:default {{ border-color: {accent}; }}

/* ── Slider ───────────────────────────────────────────────────── */
QSlider::groove:horizontal {{ background: {t.shade(t.SURFACE_2, 1.1)}; height: 4px; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {accent}; height: 4px; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: #ffffff;
    border: 3px solid {accent};
    width: 12px; height: 12px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{ background: {accent}; border-color: {accent_light}; }}

/* ── Line edit ────────────────────────────────────────────────── */
QLineEdit {{
    background: {t.INK_DEEP};
    border: 1px solid {t.LINE};
    border-radius: 6px;
    color: {t.TEXT};
    padding: 7px 11px;
    selection-background-color: {accent_dim};
    selection-color: {t.TEXT};
}}
QLineEdit:hover {{ border-color: {t.shade(t.LINE, 1.4)}; }}
QLineEdit:focus {{ border-color: {accent}; background: {t.INK}; }}
QLineEdit:disabled {{ color: {t.FAINT}; background: {t.INK}; }}

/* ── Combo box ────────────────────────────────────────────────── */
QComboBox {{
    background: {t.INK_DEEP};
    border: 1px solid {t.LINE};
    border-radius: 6px;
    color: {t.TEXT};
    padding: 7px 11px;
    min-width: 80px;
}}
QComboBox:hover {{ border-color: {t.shade(t.LINE, 1.4)}; }}
QComboBox:focus {{ border-color: {accent}; }}
QComboBox::drop-down {{ border: none; width: 24px; padding-right: 6px; }}
QComboBox QAbstractItemView {{
    background: {t.SURFACE_2};
    border: 1px solid {t.LINE};
    color: {t.TEXT};
    selection-background-color: {t.shade(accent_dim, 0.6)};
    selection-color: {accent};
    outline: none;
    padding: 4px 0;
}}

/* ── Spin boxes ───────────────────────────────────────────────── */
QDoubleSpinBox, QSpinBox {{
    background: {t.INK_DEEP};
    border: 1px solid {t.LINE};
    border-radius: 6px;
    color: {t.TEXT};
    padding: 6px 8px;
}}
QDoubleSpinBox:focus, QSpinBox:focus {{ border-color: {accent}; }}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {{
    background: {t.SURFACE_2};
    border: none;
    width: 18px;
    border-radius: 3px;
}}
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover,
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {t.shade(t.SURFACE_2, 1.2)};
}}

/* ── Scrollbars ───────────────────────────────────────────────── */
QScrollBar:vertical {{ background: transparent; width: 8px; border: none; margin: 0; }}
QScrollBar::handle:vertical {{ background: {t.LINE}; border-radius: 4px; min-height: 30px; margin: 1px; }}
QScrollBar::handle:vertical:hover {{ background: {accent_dim}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

QScrollBar:horizontal {{ background: transparent; height: 8px; border: none; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {t.LINE}; border-radius: 4px; min-width: 30px; margin: 1px; }}
QScrollBar::handle:horizontal:hover {{ background: {accent_dim}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}

/* ── Status bar ───────────────────────────────────────────────── */
QStatusBar {{
    background: {t.INK_DEEP};
    color: {t.MUTED};
    border-top: 1px solid {t.LINE};
    font-family: {t.FONT_MONO};
    font-size: 8pt;
    padding: 1px 6px;
}}

/* ── Text browser ─────────────────────────────────────────────── */
QTextBrowser {{
    background: {t.INK_DEEP};
    border: 1px solid {t.LINE};
    border-radius: 8px;
    color: {t.TEXT};
    selection-background-color: {accent_dim};
    font-size: 9pt;
}}

/* ── Check box ────────────────────────────────────────────────── */
QCheckBox {{ spacing: 8px; color: {t.MUTED}; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {t.LINE};
    border-radius: 4px;
    background: {t.INK_DEEP};
}}
QCheckBox::indicator:hover {{ border-color: {accent}; }}
QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; image: none; }}
QCheckBox::indicator:checked:hover {{ background: {accent_light}; }}

/* ── Group box ────────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {t.LINE};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    font-family: {t.FONT_DISPLAY};
    font-weight: 600;
    font-size: 8.5pt;
    color: {t.MUTED};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background: {t.INK};
    color: {t.MUTED};
    letter-spacing: 1.2px;
    text-transform: uppercase;
    font-size: 8pt;
}}

/* ── Dialogs ──────────────────────────────────────────────────── */
QDialog {{ background: {t.INK}; }}
QDialogButtonBox QPushButton {{ min-width: 84px; }}

/* ── Labels ───────────────────────────────────────────────────── */
QLabel {{ color: {t.TEXT}; background: transparent; }}

/* ── Tooltip ──────────────────────────────────────────────────── */
QToolTip {{
    background: {t.SURFACE_2};
    border: 1px solid {accent_dim};
    color: {t.TEXT};
    padding: 6px 10px;
    border-radius: 5px;
    font-size: 8.5pt;
}}

/* ── Progress ─────────────────────────────────────────────────── */
QProgressDialog {{ background: {t.INK}; }}
QProgressBar {{
    background: {t.INK_DEEP};
    border: 1px solid {t.LINE};
    border-radius: 5px;
    text-align: center;
    color: {t.TEXT};
    font-size: 8pt;
    height: 8px;
}}
QProgressBar::chunk {{ background: {accent}; border-radius: 4px; }}

/* ── Message box ──────────────────────────────────────────────── */
QMessageBox {{ background: {t.INK}; }}
QMessageBox QLabel {{ color: {t.TEXT}; }}
"""


def build_stylesheet(accent: str = theme.ACCENT) -> str:
    """Return the app stylesheet with the given accent colour applied.

    Surfaces and text come from ``theme``; only the accent (and its derived
    dim/light shades) varies, supporting the per-team accent feature.
    """
    accent_dim = theme.shade(accent, 0.62)
    accent_light = theme.shade(accent, 1.2)
    return _build(accent, accent_dim, accent_light)


APP_STYLESHEET = build_stylesheet()
