from __future__ import annotations

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget,
)


class PlayerWidget(QWidget):
    position_changed = pyqtSignal(float)  # seconds
    duration_changed = pyqtSignal(float)  # seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 0.0
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)
        self._setup_ui()
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._video_widget = QVideoWidget()
        self._video_widget.setMinimumHeight(200)
        self._player.setVideoOutput(self._video_widget)
        # Force native HWND creation so the video renderer has a valid surface.
        self._video_widget.winId()
        layout.addWidget(self._video_widget, stretch=1)

        ctrl_widget = QWidget()
        ctrl_widget.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #080c14, stop:1 #060911);"
            "border-top: 1px solid #141e2e;"
        )
        ctrl_widget.setFixedHeight(42)
        ctrl = QHBoxLayout(ctrl_widget)
        ctrl.setContentsMargins(10, 0, 10, 0)
        ctrl.setSpacing(10)

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(34, 28)
        self._play_btn.setStyleSheet(
            "QPushButton { background: #00b09b; color: #000; border: none;"
            " border-radius: 14px; font-size: 10pt; font-weight: bold; }"
            "QPushButton:hover { background: #00d4b8; }"
            "QPushButton:pressed { background: #008f7e; }"
        )
        self._play_btn.clicked.connect(self.toggle_play)
        ctrl.addWidget(self._play_btn)

        mono = QFont("Cascadia Code", 8)
        mono.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)

        self._pos_label = QLabel("00:00:00")
        self._pos_label.setFont(mono)
        self._pos_label.setStyleSheet(
            "color: #00b09b; background: transparent; min-width: 60px;"
            "letter-spacing: 0.5px;"
        )
        ctrl.addWidget(self._pos_label)

        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setRange(0, 10000)
        self._seek_slider.sliderMoved.connect(self._seek_to_slider)
        ctrl.addWidget(self._seek_slider, stretch=1)

        self._dur_label = QLabel("00:00:00")
        self._dur_label.setFont(mono)
        self._dur_label.setStyleSheet(
            "color: #4d6880; background: transparent; min-width: 60px;"
            "letter-spacing: 0.5px;"
        )
        ctrl.addWidget(self._dur_label)

        self._speed_label = QLabel("1.0×")
        self._speed_label.setFixedWidth(46)
        self._speed_label.setFont(mono)
        self._speed_label.setStyleSheet(
            "color: #4d6880; background: #0a0f1a; border: 1px solid #1a2840;"
            " border-radius: 4px; padding: 2px 5px; font-size: 8pt;"
        )
        ctrl.addWidget(self._speed_label)

        layout.addWidget(ctrl_widget)

    # ── Public API ──────────────────────────────────────────────────────

    def load(self, path: str) -> None:
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
        self._play_btn.setText("⏸")

    def toggle_play(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self._play_btn.setText("▶")
        else:
            self._player.play()
            self._play_btn.setText("⏸")

    def get_position(self) -> float:
        return self._player.position() / 1000.0

    def seek(self, seconds: float) -> None:
        self._player.setPosition(int(max(0.0, seconds) * 1000))

    def step(self, seconds: float) -> None:
        self.seek(max(0.0, self.get_position() + seconds))

    def set_rate(self, rate: float) -> None:
        rate = max(0.25, min(4.0, rate))
        self._player.setPlaybackRate(rate)
        self._speed_label.setText(f"{rate:.2g}×")

    def get_rate(self) -> float:
        return self._player.playbackRate()

    # ── Private slots ───────────────────────────────────────────────────

    def _on_position_changed(self, ms: int) -> None:
        pos = ms / 1000.0
        self.position_changed.emit(pos)
        self._pos_label.setText(self._fmt(pos))
        if self._duration > 0:
            self._seek_slider.setValue(int(pos / self._duration * 10000))

    def _on_duration_changed(self, ms: int) -> None:
        self._duration = ms / 1000.0
        self.duration_changed.emit(self._duration)
        self._dur_label.setText(self._fmt(self._duration))

    def _seek_to_slider(self, value: int) -> None:
        if self._duration > 0:
            self.seek(value / 10000.0 * self._duration)

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
