from __future__ import annotations

from typing import Callable, List, Optional

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from videotagger.ui.zoomable_video_view import ZoomableVideoView
from videotagger.core.angle_sync import needs_resync
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSlider, QStackedWidget, QVBoxLayout, QWidget,
)


class PlayerWidget(QWidget):
    position_changed = pyqtSignal(float)  # seconds (canonical / primary timeline)
    duration_changed = pyqtSignal(float)  # seconds
    angle_changed = pyqtSignal(int)       # index of the now-visible angle

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 0.0

        # Primary (canonical) player drives position/duration/slider.
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)

        # Secondary angle (lazily created). Working videos are silent, so no audio output.
        self._player2: Optional[QMediaPlayer] = None
        self._view2: Optional[ZoomableVideoView] = None
        self._mapper: Optional[Callable[[float], float]] = None
        self._angle_names: List[str] = ["Angle 1", "Angle 2"]
        self._current_angle = 0

        self._setup_ui()
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Both angle views live in a stack; only the active one is shown. Both players
        # keep decoding so switching is instant (no reload).
        self._zoom_view = ZoomableVideoView()
        self._zoom_view.setMinimumHeight(200)
        self._player.setVideoOutput(self._zoom_view.video_item)
        self._view_stack = QStackedWidget()
        self._view_stack.addWidget(self._zoom_view)
        layout.addWidget(self._view_stack, stretch=1)

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

        # Angle toggle — hidden until a secondary angle is loaded.
        self._angle_btn = QPushButton()
        self._angle_btn.setFont(mono)
        self._angle_btn.setStyleSheet(
            "QPushButton { color: #00b09b; background: #0a0f1a;"
            " border: 1px solid #1a2840; border-radius: 4px; padding: 2px 8px;"
            " font-size: 8pt; }"
            "QPushButton:hover { border-color: #00b09b; }"
        )
        self._angle_btn.clicked.connect(self.switch_angle)
        self._angle_btn.setVisible(False)
        ctrl.addWidget(self._angle_btn)

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

    def set_secondary_angle(
        self,
        path: str,
        mapper: Callable[[float], float],
        primary_name: str = "Angle 1",
        secondary_name: str = "Angle 2",
    ) -> None:
        """Load a second camera angle that plays locked to the primary timeline.

        ``mapper`` converts a canonical (primary) time in seconds to this angle's video
        time in seconds. Both players decode simultaneously so switching is instant.
        """
        self._mapper = mapper
        self._angle_names = [primary_name, secondary_name]

        if self._player2 is None:
            self._view2 = ZoomableVideoView()
            self._view2.setMinimumHeight(200)
            self._player2 = QMediaPlayer(self)
            self._player2.setVideoOutput(self._view2.video_item)
            self._view_stack.addWidget(self._view2)

        self._player2.setSource(QUrl.fromLocalFile(path))
        self._player2.setPlaybackRate(self._player.playbackRate())
        # Align to the current primary position, then match play/pause state.
        self._player2.setPosition(int(mapper(self.get_position()) * 1000))
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player2.play()

        self._angle_btn.setVisible(True)
        self._update_angle_button()

    def clear_secondary_angle(self) -> None:
        """Remove the secondary angle and return to single-angle playback."""
        if self._current_angle != 0:
            self.switch_angle()
        if self._player2 is not None:
            self._player2.stop()
            self._player2.setVideoOutput(None)
            self._player2.deleteLater()
            self._player2 = None
        if self._view2 is not None:
            self._view_stack.removeWidget(self._view2)
            self._view2.deleteLater()
            self._view2 = None
        self._mapper = None
        self._angle_btn.setVisible(False)

    def switch_angle(self) -> None:
        if self._player2 is None:
            return
        self._current_angle = 1 - self._current_angle
        self._view_stack.setCurrentIndex(self._current_angle)
        self._update_angle_button()
        self.angle_changed.emit(self._current_angle)

    def has_secondary_angle(self) -> bool:
        return self._player2 is not None

    def toggle_play(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            if self._player2 is not None:
                self._player2.pause()
            self._play_btn.setText("▶")
        else:
            self._player.play()
            if self._player2 is not None:
                self._player2.play()
            self._play_btn.setText("⏸")

    def get_position(self) -> float:
        return self._player.position() / 1000.0

    def seek(self, seconds: float) -> None:
        seconds = max(0.0, seconds)
        self._player.setPosition(int(seconds * 1000))
        if self._player2 is not None and self._mapper is not None:
            self._player2.setPosition(int(self._mapper(seconds) * 1000))

    def step(self, seconds: float) -> None:
        self.seek(max(0.0, self.get_position() + seconds))

    def set_rate(self, rate: float) -> None:
        rate = max(0.25, min(4.0, rate))
        self._player.setPlaybackRate(rate)
        if self._player2 is not None:
            self._player2.setPlaybackRate(rate)
        self._speed_label.setText(f"{rate:.2g}×")

    def get_rate(self) -> float:
        return self._player.playbackRate()

    def zoom_in(self) -> None:
        self._current_view().zoom_in()

    def zoom_out(self) -> None:
        self._current_view().zoom_out()

    def reset_zoom(self) -> None:
        self._current_view().reset_zoom()

    # ── Private slots ───────────────────────────────────────────────────

    def _current_view(self) -> ZoomableVideoView:
        if self._current_angle == 1 and self._view2 is not None:
            return self._view2
        return self._zoom_view

    def _update_angle_button(self) -> None:
        self._angle_btn.setText(f"📹 {self._angle_names[self._current_angle]}")

    def _on_position_changed(self, ms: int) -> None:
        pos = ms / 1000.0
        self.position_changed.emit(pos)
        self._pos_label.setText(self._fmt(pos))
        if self._duration > 0:
            # Block signals while following playback: setValue() re-emits
            # sliderMoved when the slider is pressed (mid-drag), which would feed
            # back into _seek_to_slider -> seek -> setPosition and recurse.
            was_blocked = self._seek_slider.blockSignals(True)
            self._seek_slider.setValue(int(pos / self._duration * 10000))
            self._seek_slider.blockSignals(was_blocked)
        self._correct_drift(pos)

    def _correct_drift(self, pos: float) -> None:
        """Keep the secondary angle locked to the mapped primary position while playing."""
        if self._player2 is None or self._mapper is None:
            return
        if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            return
        expected = self._mapper(pos)
        actual = self._player2.position() / 1000.0
        if needs_resync(expected, actual):
            self._player2.setPosition(int(expected * 1000))

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
