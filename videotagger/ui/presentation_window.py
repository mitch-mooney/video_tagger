from __future__ import annotations

from typing import List

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QLabel, QPushButton, QWidget

from videotagger.models.project import Clip


class PresentationWindow(QWidget):
    closed = pyqtSignal()

    def __init__(self, video_path: str, clips: List[Clip], playlist_name: str,
                 category_map: dict | None = None, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Presentation Mode")
        self.setStyleSheet("background: black;")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._video_path = video_path
        self._clips = clips
        self._playlist_name = playlist_name
        self._category_map: dict = category_map or {}
        self._current_index = 0
        self._notes_pinned = False
        self._ui_ready = False
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)
        self._setup_ui()
        self._ui_ready = True
        self._setup_timers()
        self._player.positionChanged.connect(self._on_position_changed)

    # ── UI setup ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        self._video_widget = QVideoWidget(self)
        self._video_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._player.setVideoOutput(self._video_widget)
        self._video_widget.winId()

        self._pinned_notes = QLabel("", self)
        self._pinned_notes.setStyleSheet(
            "color:#ffe066; background:rgba(0,0,0,185);"
            "padding:8px 14px; border-radius:5px; border:1px solid rgba(255,220,80,130);"
        )
        self._pinned_notes.setFont(QFont("Arial", 13))
        self._pinned_notes.setWordWrap(True)
        self._pinned_notes.setMaximumWidth(700)
        self._pinned_notes.hide()

        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._hud.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        hud_s = "color:white; background:rgba(0,0,0,160); padding:4px 8px; border-radius:3px;"

        self._name_label = QLabel(self._playlist_name, self._hud)
        self._name_label.setStyleSheet(hud_s)
        self._name_label.setFont(QFont("Arial", 12))
        self._name_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._clip_label = QLabel("", self._hud)
        self._clip_label.setStyleSheet(hud_s)
        self._clip_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self._clip_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._notes_label = QLabel("", self._hud)
        self._notes_label.setStyleSheet(
            "color:#cccccc; background:rgba(0,0,0,140); padding:3px 8px; border-radius:3px;"
        )
        self._notes_label.setFont(QFont("Arial", 11))
        self._notes_label.setWordWrap(True)
        self._notes_label.setMaximumWidth(600)
        self._notes_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._counter_label = QLabel("", self._hud)
        self._counter_label.setStyleSheet(hud_s)
        self._counter_label.setFont(QFont("Arial", 12))
        self._counter_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._shortcut_hint = QLabel(
            "[N] Pin notes   [Tab] Next   [Shift+Tab] Prev   [Space] Play   [Esc] Exit",
            self._hud,
        )
        self._shortcut_hint.setStyleSheet(
            "color:rgba(255,255,255,110); background:transparent; font-size:8pt;"
        )
        self._shortcut_hint.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        btn_s = (
            "color:white; background:rgba(0,0,0,160); border:none;"
            "font-size:20px; padding:6px 12px; border-radius:3px;"
        )
        self._prev_btn = QPushButton("\u23ee", self._hud)
        self._play_btn = QPushButton("\u23f8", self._hud)
        self._next_btn = QPushButton("\u23ed", self._hud)
        for btn in (self._prev_btn, self._play_btn, self._next_btn):
            btn.setStyleSheet(btn_s)
            btn.setFixedSize(50, 40)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._prev_btn.clicked.connect(self._prev_clip)
        self._play_btn.clicked.connect(self._toggle_play)
        self._next_btn.clicked.connect(self._next_clip)

        self.setMouseTracking(True)

    def _setup_timers(self):
        self._hud_timer = QTimer(self)
        self._hud_timer.setSingleShot(True)
        self._hud_timer.setInterval(3000)
        self._hud_timer.timeout.connect(self._hide_hud)

    # ── Qt lifecycle ──────────────────────────────────────────────────────

    def showFullScreen(self):
        super().showFullScreen()
        QTimer.singleShot(0, lambda: self._play_clip(0))
        self._show_hud()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._ui_ready:
            return
        self._video_widget.resize(self.size())
        self._hud.resize(self.size())
        self._reposition_hud()

    # ── Layout ────────────────────────────────────────────────────────────

    def _reposition_hud(self):
        w, h = self.width(), self.height()

        self._name_label.adjustSize()
        self._name_label.move(12, 12)

        self._clip_label.adjustSize()
        self._clip_label.move(12, h - 72)

        notes_visible = bool(self._notes_label.text()) and not self._notes_pinned
        self._notes_label.setVisible(notes_visible)
        self._notes_label.adjustSize()
        self._notes_label.move(12, h - 50)

        self._counter_label.adjustSize()
        self._counter_label.move(w - self._counter_label.width() - 12, h - 72)

        cx = (w - 160) // 2
        self._prev_btn.move(cx, h - 52)
        self._play_btn.move(cx + 55, h - 52)
        self._next_btn.move(cx + 110, h - 52)

        self._pinned_notes.setMaximumWidth(min(700, w - 24))
        self._pinned_notes.adjustSize()
        self._pinned_notes.move(12, h - 100 - self._pinned_notes.height())

        self._shortcut_hint.adjustSize()
        self._shortcut_hint.move(w - self._shortcut_hint.width() - 12, 12)

    # ── Playback ──────────────────────────────────────────────────────────

    def _play_clip(self, index: int):
        if not self._clips or index < 0 or index >= len(self._clips):
            return
        self._current_index = index
        clip = self._clips[index]
        self._player.setSource(QUrl.fromLocalFile(self._video_path))
        self._player.play()
        QTimer.singleShot(300, lambda: self._seek_to(clip.start))
        self._play_btn.setText("\u23f8")
        self._update_hud_labels()
        QTimer.singleShot(400, self.setFocus)

    def _seek_to(self, t: float):
        self._player.setPosition(int(t * 1000))

    def _on_position_changed(self, ms: int):
        if not self._clips:
            return
        clip = self._clips[self._current_index]
        if ms / 1000.0 >= clip.end:
            self._player.pause()
            if self._current_index + 1 < len(self._clips):
                QTimer.singleShot(800, lambda: self._play_clip(self._current_index + 1))
            else:
                self._play_btn.setText("\u25b6")

    def _update_hud_labels(self):
        if not self._clips:
            return
        clip = self._clips[self._current_index]
        cat_name = self._category_map.get(clip.category_id, "")
        label_text = f"{cat_name} — {clip.label}" if cat_name else clip.label
        self._clip_label.setText(label_text)
        notes_text = clip.notes.strip() if clip.notes else ""
        self._notes_label.setText(notes_text)
        self._pinned_notes.setText(notes_text)
        self._pinned_notes.setVisible(self._notes_pinned and bool(notes_text))
        self._counter_label.setText(f"{self._current_index + 1} / {len(self._clips)}")
        self._reposition_hud()

    def _toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self._play_btn.setText("\u25b6")
        else:
            self._player.play()
            self._play_btn.setText("\u23f8")
        self.setFocus()

    def _prev_clip(self):
        self._play_clip(max(0, self._current_index - 1))

    def _next_clip(self):
        self._play_clip(min(len(self._clips) - 1, self._current_index + 1))

    def _step(self, seconds: float):
        if not self._clips:
            return
        clip = self._clips[self._current_index]
        current = self._player.position() / 1000.0
        target = max(clip.start, min(clip.end - 0.1, current + seconds))
        self._seek_to(target)

    def _frame_step(self, direction: int):
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self._play_btn.setText("\u25b6")
        if direction > 0:
            self._player.setPosition(self._player.position() + 40)
        else:
            self._step(-0.04)

    def _set_rate(self, delta: float):
        rate = max(0.25, min(4.0, self._player.playbackRate() + delta))
        self._player.setPlaybackRate(rate)

    # ── HUD ───────────────────────────────────────────────────────────────

    def _hide_hud(self):
        self._hud.setVisible(False)

    def _show_hud(self):
        self._hud.setVisible(True)
        self._hud_timer.start()

    # ── Notes pin ─────────────────────────────────────────────────────────

    def _toggle_notes_pin(self):
        self._notes_pinned = not self._notes_pinned
        notes_text = self._notes_label.text()
        self._pinned_notes.setVisible(self._notes_pinned and bool(notes_text))
        if self._notes_pinned:
            self._pinned_notes.raise_()
        self._reposition_hud()
        self._show_hud()

    # ── Mouse / keyboard ──────────────────────────────────────────────────

    def mousePressEvent(self, event):
        self.setFocus()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self._show_hud()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if key in (Qt.Key.Key_Escape, Qt.Key.Key_F11):
            self._hud_timer.stop()
            self._player.stop()
            self.closed.emit()
            self.close()

        elif key == Qt.Key.Key_Space:
            self._toggle_play()

        elif key == Qt.Key.Key_Tab:
            self._next_clip()

        elif key == Qt.Key.Key_Backtab:
            self._prev_clip()

        elif key == Qt.Key.Key_Left:
            self._step(-5)

        elif key == Qt.Key.Key_Right:
            self._step(5)

        elif key in (Qt.Key.Key_Comma, Qt.Key.Key_Less):
            self._frame_step(-1)

        elif key in (Qt.Key.Key_Period, Qt.Key.Key_Greater):
            self._frame_step(1)

        elif key == Qt.Key.Key_BracketLeft:
            self._set_rate(-0.25)

        elif key == Qt.Key.Key_BracketRight:
            self._set_rate(0.25)

        elif key == Qt.Key.Key_N:
            self._toggle_notes_pin()

        else:
            super().keyPressEvent(event)
