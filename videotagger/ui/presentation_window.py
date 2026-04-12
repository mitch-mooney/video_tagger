# videotagger/ui/presentation_window.py
from __future__ import annotations
import sys
import vlc
from typing import List
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QKeyEvent, QFont, QPainter, QPen, QColor, QPixmap
from videotagger.models.project import Clip


class DrawingOverlay(QWidget):
    """Transparent overlay that captures freehand pen strokes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._canvas: QPixmap | None = None
        self._last_pos: QPoint | None = None
        self._pen_color = QColor("#ff4444")
        self._pen_width = 4

    def resizeEvent(self, event):
        # Preserve existing strokes scaled to new size (simple: recreate blank)
        new_canvas = QPixmap(self.size())
        new_canvas.fill(Qt.GlobalColor.transparent)
        if self._canvas:
            painter = QPainter(new_canvas)
            painter.drawPixmap(0, 0, self._canvas)
            painter.end()
        self._canvas = new_canvas
        super().resizeEvent(event)

    def clear(self):
        if self._canvas:
            self._canvas.fill(Qt.GlobalColor.transparent)
        self.update()

    def paintEvent(self, event):
        if self._canvas:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self._canvas)
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._last_pos is not None:
            if self._canvas is None:
                self._canvas = QPixmap(self.size())
                self._canvas.fill(Qt.GlobalColor.transparent)
            painter = QPainter(self._canvas)
            pen = QPen(self._pen_color, self._pen_width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self._last_pos, event.position().toPoint())
            painter.end()
            self._last_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        self._last_pos = None

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

        # Drawing overlay (below HUD so HUD buttons remain clickable)
        self._drawing = DrawingOverlay(self)
        self._drawing.hide()
        self._drawing_mode = False

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

        self._notes_label = QLabel("", self._hud)
        self._notes_label.setStyleSheet(
            "color: #cccccc; background: rgba(0,0,0,140); padding: 3px 8px; border-radius: 3px;"
        )
        self._notes_label.setFont(QFont("Arial", 11))
        self._notes_label.setWordWrap(True)
        self._notes_label.setMaximumWidth(600)

        self._counter_label = QLabel("", self._hud)
        self._counter_label.setStyleSheet(hud_style)
        self._counter_label.setFont(QFont("Arial", 12))

        self._draw_label = QLabel("✏ DRAW MODE  [C] clear  [D] exit", self._hud)
        self._draw_label.setStyleSheet(
            "color: #ff4444; background: rgba(0,0,0,160); padding: 3px 8px; border-radius: 3px;"
        )
        self._draw_label.setFont(QFont("Arial", 11))
        self._draw_label.hide()

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
        self._drawing.resize(self.size())
        self._hud.resize(self.size())
        self._reposition_hud()

    def _reposition_hud(self):
        w, h = self.width(), self.height()
        self._name_label.adjustSize()
        self._name_label.move(12, 12)

        self._clip_label.adjustSize()
        self._clip_label.move(12, h - 72)

        self._notes_label.adjustSize()
        self._notes_label.move(12, h - 50)
        self._notes_label.setVisible(bool(self._notes_label.text()))

        self._counter_label.adjustSize()
        self._counter_label.move(w - self._counter_label.width() - 12, h - 72)

        cx = (w - 160) // 2
        self._prev_btn.move(cx, h - 52)
        self._play_btn.move(cx + 55, h - 52)
        self._next_btn.move(cx + 110, h - 52)

        self._draw_label.adjustSize()
        self._draw_label.move((w - self._draw_label.width()) // 2, 12)

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
        self._notes_label.setText(clip.notes.strip() if clip.notes else "")
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

    def _toggle_drawing(self):
        self._drawing_mode = not self._drawing_mode
        self._drawing.setVisible(self._drawing_mode)
        self._draw_label.setVisible(self._drawing_mode)
        # In draw mode, HUD buttons stay accessible; mouse events go to drawing overlay
        if self._drawing_mode:
            self._drawing.raise_()
            self._hud.raise_()
            self._show_hud()
        else:
            self._hud_timer.start()

    def mouseMoveEvent(self, event):
        if not self._drawing_mode:
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
        elif key == Qt.Key.Key_D:
            self._toggle_drawing()
        elif key == Qt.Key.Key_C and self._drawing_mode:
            self._drawing.clear()
        elif key == Qt.Key.Key_Space:
            self._toggle_play()
        elif key == Qt.Key.Key_Left and not self._drawing_mode:
            self._prev_clip()
        elif key == Qt.Key.Key_Right and not self._drawing_mode:
            self._next_clip()
        else:
            super().keyPressEvent(event)
