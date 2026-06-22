# videotagger/ui/shortcut_bar.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

from videotagger.ui import theme

_IDLE_HINTS = [
    ("I", "Mark In"),
    ("O", "Mark Out"),
    ("Space", "Play"),
    ("← →", "±5s"),
    ("⇧← →", "Frame"),
    ("[ ]", "Speed"),
    ("+ −", "Zoom"),
    ("0", "Reset Zoom"),
    ("Ctrl+Z", "Undo"),
]

_MARKING_HINTS = [
    ("O", "Mark Out"),
    ("Esc", "Cancel"),
]


def _key(k: str, signal: bool = False) -> str:
    if signal:
        color = theme.SIGNAL
        border = f'1px solid {theme.SIGNAL_DIM}'
    else:
        color = theme.ACCENT
        border = f'1px solid {theme.LINE}'
    return (
        f'<span style="'
        f'background:{theme.SURFACE_2};'
        f'color:{color};'
        f'border:{border};'
        f'border-bottom:2px solid {theme.INK_DEEP};'
        f'border-radius:4px;'
        f'padding:0px 6px;'
        f'font-family:{theme.FONT_MONO};'
        f'font-size:7.5pt;'
        f'font-weight:600;'
        f'">{k}</span>'
    )


def _hint(k: str, label: str, signal: bool = False) -> str:
    return (
        f'{_key(k, signal=signal)}'
        f'<span style="color:{theme.FAINT};font-size:8pt;"> {label}</span>'
    )


class ShortcutBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {theme.INK_DEEP}, stop:1 {theme.INK_DEEP});"
            f"border-top: 1px solid {theme.LINE};"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(14)
        self._label = QLabel()
        self._label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._label)
        layout.addStretch()
        self._state_label = QLabel()
        self._state_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._state_label)
        self._has_angle = False
        self._is_idle = True
        self.set_idle()

    def set_angle_available(self, available: bool):
        """Show/hide the angle-switch hint when a second camera angle is loaded."""
        self._has_angle = available
        if self._is_idle:
            self.set_idle()

    def set_idle(self):
        self._is_idle = True
        hints = list(_IDLE_HINTS)
        if self._has_angle:
            hints.append(("V", "Angle"))
        text = "&nbsp; &nbsp;".join(
            _hint(k, v, signal=k in ("I", "O")) for k, v in hints
        )
        self._label.setText(text)
        self._state_label.setText("")

    def set_marking(self, start_time: float):
        self._is_idle = False
        hints = "&nbsp; &nbsp;".join(
            _hint(k, v, signal=k in ("I", "O")) for k, v in _MARKING_HINTS
        )
        self._label.setText(hints)
        self._state_label.setText(
            f'<span style="'
            f'color:{theme.SIGNAL};font-family:{theme.FONT_DISPLAY};font-size:8pt;'
            f'font-weight:700;letter-spacing:1.5px;text-transform:uppercase;">'
            f'⬤ MARKING</span>'
            f'<span style="color:{theme.MUTED};font-size:7.5pt;font-family:{theme.FONT_MONO};">'
            f'&nbsp; IN @ {start_time:.2f}s</span>'
        )
