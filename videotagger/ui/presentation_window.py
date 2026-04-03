# videotagger/ui/presentation_window.py
from __future__ import annotations
import sys
import vlc
from typing import List
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QFont
from videotagger.models.project import Clip

class PresentationWindow(QWidget):
    closed = pyqtSignal()

    def __init__(self, video_path: str, clips: List[Clip], playlist_name: str,
                 category_map: dict | None = None, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Presentation Mode")
        self.setStyleSheet("background: black;")
        self._video_path = video_path
        self._clips = clips
        self._playlist_name = playlist_name
        self._category_map: dict = category_map or {}
        self._current_index = 0
        self._instance = None
        self._player = None
        self._setup_ui()
        self._setup_timers()

    def _init_vlc(self):
        """Lazily initialise VLC — called on first show so the window handle exists."""
        if self._instance is not None:
            return
        args = ["--no-plugins-cache"]
        if sys.platform == "linux":
            args.append("--no-xlib")
        self._instance = vlc.Instance(*args)
        self._player = self._instance.media_player_new()

    def _attach_vlc_window(self):
        """Attach VLC to this widget's native window handle. Called after show()."""
        if sys.platform == "win32":
            self._player.set_hwnd(int(self.winId()))
        elif sys.platform == "darwin":
            self._player.set_nsobject(int(self.winId()))
        else:
            self._player.set_xwindow(int(self.winId()))

    def _setup_ui(self):
        # No layout manager — child widgets use absolute positioning for HUD overlay

        # HUD overlay
        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        hud_style = "color: white; background: rgba(0,0,0,160); padding: 4px 8px; border-radius: 3px;"

        self._name_label = QLabel(self._playlist_name, self._hud)
        self._name_label.setStyleSheet(hud_style)
        self._name_label.setFont(QFont("Arial", 12))

        self._clip_label = QLabel("", self._hud)
        self._clip_label.setStyleSheet(hud_style)
        self._clip_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        self._counter_label = QLabel("", self._hud)
        self._counter_label.setStyleSheet(hud_style)
        self._counter_label.setFont(QFont("Arial", 12))

        btn_style = "color: white; background: rgba(0,0,0,160); border: none; font-size: 20px; padding: 6px 12px; border-radius: 3px;"
        self._prev_btn = QPushButton("\u23ee", self._hud)
        self._play_btn = QPushButton("\u23f8", self._hud)
        self._next_btn = QPushButton("\u23ed", self._hud)
        for btn in [self._prev_btn, self._play_btn, self._next_btn]:
            btn.setStyleSheet(btn_style)
            btn.setFixedSize(50, 40)
        self._prev_btn.clicked.connect(self._prev_clip)
        self._play_btn.clicked.connect(self._toggle_play)
        self._next_btn.clicked.connect(self._next_clip)

        self.setMouseTracking(True)

    def _setup_timers(self):
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(200)
        self._poll_timer.timeout.connect(self._check_clip_end)

        self._hud_timer = QTimer(self)
        self._hud_timer.setSingleShot(True)
        self._hud_timer.setInterval(3000)
        self._hud_timer.timeout.connect(self._hide_hud)

    def showEvent(self, event):
        super().showEvent(event)
        self._init_vlc()
        self._attach_vlc_window()

    def showFullScreen(self):
        super().showFullScreen()
        QTimer.singleShot(0, lambda: self._play_clip(0))
        self._show_hud()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.resize(self.size())
        self._reposition_hud()

    def _reposition_hud(self):
        w, h = self.width(), self.height()
        self._name_label.adjustSize()
        self._name_label.move(12, 12)

        self._clip_label.adjustSize()
        self._clip_label.move(12, h - 50)

        self._counter_label.adjustSize()
        self._counter_label.move(w - self._counter_label.width() - 12, h - 50)

        cx = (w - 160) // 2
        self._prev_btn.move(cx, h - 52)
        self._play_btn.move(cx + 55, h - 52)
        self._next_btn.move(cx + 110, h - 52)

    def _play_clip(self, index: int):
        if self._player is None or not self._clips or index < 0 or index >= len(self._clips):
            return
        self._current_index = index
        clip = self._clips[index]
        media = self._instance.media_new(self._video_path)
        self._player.set_media(media)
        self._player.play()
        # Seek after brief delay to allow media to load
        QTimer.singleShot(200, lambda: self._player.set_time(int(clip.start * 1000)))
        self._poll_timer.start()
        self._update_hud_labels()

    def _check_clip_end(self):
        if self._player is None or not self._clips:
            return
        clip = self._clips[self._current_index]
        current_time = self._player.get_time() / 1000.0
        if current_time >= clip.end:
            self._poll_timer.stop()
            if self._current_index + 1 < len(self._clips):
                QTimer.singleShot(1000, lambda: self._play_clip(self._current_index + 1))
            else:
                self._player.pause()
                self._play_btn.setText("\u25b6")

    def _update_hud_labels(self):
        if not self._clips:
            return
        clip = self._clips[self._current_index]
        cat_name = self._category_map.get(clip.category_id, "")
        label_text = f"{cat_name} — {clip.label}" if cat_name else clip.label
        self._clip_label.setText(label_text)
        self._counter_label.setText(f"{self._current_index + 1} / {len(self._clips)}")
        self._reposition_hud()

    def _toggle_play(self):
        if self._player is None:
            return
        if self._player.is_playing():
            self._player.pause()
            self._play_btn.setText("\u25b6")
        else:
            self._player.play()
            self._play_btn.setText("\u23f8")

    def _prev_clip(self):
        self._poll_timer.stop()
        self._play_clip(max(0, self._current_index - 1))

    def _next_clip(self):
        self._poll_timer.stop()
        self._play_clip(min(len(self._clips) - 1, self._current_index + 1))

    def _hide_hud(self):
        self._hud.setVisible(False)

    def _show_hud(self):
        self._hud.setVisible(True)
        self._hud_timer.start()

    def mouseMoveEvent(self, event):
        self._show_hud()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key.Key_Escape, Qt.Key.Key_F11):
            self._poll_timer.stop()
            self._hud_timer.stop()
            if self._player is not None:
                self._player.stop()
            self.closed.emit()
            self.close()
        elif key == Qt.Key.Key_Space:
            self._toggle_play()
        elif key == Qt.Key.Key_Left:
            self._prev_clip()
        elif key == Qt.Key.Key_Right:
            self._next_clip()
        else:
            super().keyPressEvent(event)
