# videotagger/ui/player_widget.py
import sys
import vlc
from PyQt6.QtWidgets import QWidget, QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

class PlayerWidget(QWidget):
    position_changed = pyqtSignal(float)
    duration_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._instance = vlc.Instance("--no-xlib")
        self._player = self._instance.media_player_new()
        self._duration = 0.0
        self._setup_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._poll_position)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._frame = QFrame()
        self._frame.setStyleSheet("background: black;")
        self._frame.setMinimumHeight(200)
        layout.addWidget(self._frame, stretch=1)

        ctrl = QHBoxLayout()
        ctrl.setContentsMargins(4, 2, 4, 2)

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedWidth(36)
        self._play_btn.clicked.connect(self.toggle_play)
        ctrl.addWidget(self._play_btn)

        self._pos_label = QLabel("00:00:00")
        self._pos_label.setFont(QFont("Courier", 9))
        ctrl.addWidget(self._pos_label)

        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setRange(0, 10000)
        self._seek_slider.sliderMoved.connect(self._seek_to_slider)
        ctrl.addWidget(self._seek_slider, stretch=1)

        self._dur_label = QLabel("00:00:00")
        self._dur_label.setFont(QFont("Courier", 9))
        ctrl.addWidget(self._dur_label)

        self._speed_label = QLabel("1.0x")
        self._speed_label.setFixedWidth(40)
        ctrl.addWidget(self._speed_label)

        layout.addLayout(ctrl)

    def load(self, path: str) -> None:
        media = self._instance.media_new(path)
        self._player.set_media(media)
        if sys.platform == "win32":
            self._player.set_hwnd(int(self._frame.winId()))
        elif sys.platform == "darwin":
            self._player.set_nsobject(int(self._frame.winId()))
        else:
            self._player.set_xwindow(int(self._frame.winId()))
        self._player.play()
        self._timer.start()
        QTimer.singleShot(500, self._update_duration)

    def _update_duration(self):
        ms = self._player.get_length()
        if ms > 0:
            self._duration = ms / 1000.0
            self.duration_changed.emit(self._duration)
            self._dur_label.setText(self._fmt(self._duration))
        else:
            QTimer.singleShot(300, self._update_duration)

    def toggle_play(self):
        if self._player.is_playing():
            self._player.pause()
            self._play_btn.setText("▶")
        else:
            self._player.play()
            self._play_btn.setText("⏸")

    def get_position(self) -> float:
        ms = self._player.get_time()
        return ms / 1000.0 if ms >= 0 else 0.0

    def seek(self, seconds: float) -> None:
        self._player.set_time(int(max(0.0, seconds) * 1000))

    def step(self, seconds: float) -> None:
        self.seek(max(0.0, self.get_position() + seconds))

    def set_rate(self, rate: float) -> None:
        rate = max(0.25, min(4.0, rate))
        self._player.set_rate(rate)
        self._speed_label.setText(f"{rate:.2g}x")

    def get_rate(self) -> float:
        return self._player.get_rate()

    def _poll_position(self):
        state = self._player.get_state()
        if state in (vlc.State.Playing, vlc.State.Paused):
            pos = self.get_position()
            self.position_changed.emit(pos)
            self._pos_label.setText(self._fmt(pos))
            if self._duration > 0:
                self._seek_slider.setValue(int(pos / self._duration * 10000))

    def _seek_to_slider(self, value: int):
        if self._duration > 0:
            self.seek(value / 10000.0 * self._duration)

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
