# videotagger/ui/shortcut_bar.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

_IDLE_HINTS = [
    ("I", "Mark In"),
    ("O", "Mark Out"),
    ("Space", "Play/Pause"),
    ("← →", "Step 5s"),
    ("Shift+← →", "Frame step"),
    ("[ ]", "Speed"),
    ("Ctrl+Z", "Undo"),
    ("Esc", "Cancel"),
]

_MARKING_HINTS = [
    ("O", "Mark Out — end clip"),
    ("Esc", "Cancel mark"),
]


def _key(k: str) -> str:
    return (
        f'<span style="background:#1e2a38;color:#00b09b;border:1px solid #00b09b;'
        f'border-radius:3px;padding:1px 5px;font-family:Consolas;font-size:8pt;">'
        f'{k}</span>'
    )


def _hint(k: str, label: str) -> str:
    return f'{_key(k)}&nbsp;<span style="color:#7d8fa3;font-size:8pt;">{label}</span>'


class ShortcutBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(26)
        self.setStyleSheet("background:#090d12; border-top:1px solid #1e2a38;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(16)
        self._label = QLabel()
        self._label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._label)
        layout.addStretch()
        self._state_label = QLabel()
        self._state_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._state_label)
        self.set_idle()

    def set_idle(self):
        hints = "  ".join(_hint(k, v) for k, v in _IDLE_HINTS)
        self._label.setText(hints)
        self._state_label.setText("")

    def set_marking(self, start_time: float):
        hints = "  ".join(_hint(k, v) for k, v in _MARKING_HINTS)
        self._label.setText(hints)
        self._state_label.setText(
            f'<span style="color:#00b09b;font-size:8pt;font-weight:bold;">'
            f'● MARKING — IN at {start_time:.2f}s</span>'
        )
