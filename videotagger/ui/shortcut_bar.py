# videotagger/ui/shortcut_bar.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

_IDLE_HINTS = [
    ("I", "Mark In"),
    ("O", "Mark Out"),
    ("Space", "Play"),
    ("← →", "±5s"),
    ("⇧← →", "Frame"),
    ("[ ]", "Speed"),
    ("Ctrl+Z", "Undo"),
]

_MARKING_HINTS = [
    ("O", "Mark Out"),
    ("Esc", "Cancel"),
]


def _key(k: str) -> str:
    return (
        f'<span style="'
        f'background:#0a1828;'
        f'color:#00b09b;'
        f'border:1px solid #1a3a50;'
        f'border-bottom:2px solid #0d2a40;'
        f'border-radius:4px;'
        f'padding:0px 6px;'
        f'font-family:Cascadia Code,Consolas,monospace;'
        f'font-size:7.5pt;'
        f'font-weight:600;'
        f'">{k}</span>'
    )


def _hint(k: str, label: str) -> str:
    return (
        f'{_key(k)}'
        f'<span style="color:#364e64;font-size:8pt;"> {label}</span>'
    )


class ShortcutBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #070b12, stop:1 #060911);"
            "border-top: 1px solid #0f1828;"
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
        self.set_idle()

    def set_idle(self):
        hints = "&nbsp; &nbsp;".join(_hint(k, v) for k, v in _IDLE_HINTS)
        self._label.setText(hints)
        self._state_label.setText("")

    def set_marking(self, start_time: float):
        hints = "&nbsp; &nbsp;".join(_hint(k, v) for k, v in _MARKING_HINTS)
        self._label.setText(hints)
        self._state_label.setText(
            f'<span style="'
            f'color:#00b09b;font-size:7.5pt;font-weight:700;letter-spacing:1px;">'
            f'⬤ MARKING</span>'
            f'<span style="color:#4d6880;font-size:7.5pt;font-family:Cascadia Code,Consolas,monospace;">'
            f'&nbsp; IN @ {start_time:.2f}s</span>'
        )
