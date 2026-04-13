# videotagger/ui/presentation_window.py
from __future__ import annotations
import sys
import vlc
from typing import List
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QKeyEvent, QFont, QPainter, QPen, QColor, QPixmap
from videotagger.models.project import Clip

_PEN_COLORS = ["#ff4444", "#ffcc00", "#44aaff", "#44ff88", "#ffffff"]


class DrawingOverlay(QWidget):
    """Transparent freehand pen overlay. Never steals keyboard focus."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._canvas: QPixmap | None = None
        self._last_pos: QPoint | None = None
        self._color_index = 0
        self._pen_color = QColor(_PEN_COLORS[0])
        self._pen_width = 4

    def cycle_color(self):
        self._color_index = (self._color_index + 1) % len(_PEN_COLORS)
        self._pen_color = QColor(_PEN_COLORS[self._color_index])
        return self._pen_color

    def thicker(self):
        self._pen_width = min(20, self._pen_width + 2)

    def thinner(self):
        self._pen_width = max(2, self._pen_width - 2)

    def clear(self):
        if self._canvas:
            self._canvas.fill(Qt.GlobalColor.transparent)
        self.update()

    def resizeEvent(self, event):
        new_canvas = QPixmap(self.size())
        new_canvas.fill(Qt.GlobalColor.transparent)
        if self._canvas:
            p = QPainter(new_canvas)
            p.drawPixmap(0, 0, self._canvas)
            p.end()
        self._canvas = new_canvas
        super().resizeEvent(event)

    def paintEvent(self, event):
        if self._canvas:
            p = QPainter(self)
            p.drawPixmap(0, 0, self._canvas)
            p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_pos = event.position().toPoint()
        # Ensure parent keeps focus so keyboard shortcuts still work
        if self.parent():
            self.parent().setFocus()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton) or self._last_pos is None:
            return
        if self._canvas is None:
            self._canvas = QPixmap(self.size())
            self._canvas.fill(Qt.GlobalColor.transparent)
        p = QPainter(self._canvas)
        pen = QPen(self._pen_color, self._pen_width,
                   Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawLine(self._last_pos, event.position().toPoint())
        p.end()
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
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._video_path = video_path
        self._clips = clips
        self._playlist_name = playlist_name
        self._category_map: dict = category_map or {}
        self._current_index = 0
        self._instance = None
        self._player = None
        self._drawing_mode = False
        self._notes_pinned = False
        self._setup_ui()
        self._setup_timers()

    # ── VLC ───────────────────────────────────────────────────────────────

    def _init_vlc(self):
        if self._instance is not None:
            return
        args = ["--no-plugins-cache"]
        if sys.platform == "linux":
            args.append("--no-xlib")
        self._instance = vlc.Instance(*args)
        self._player = self._instance.media_player_new()
        # Tell VLC not to handle keyboard or mouse input — Qt handles everything
        self._player.video_set_key_input(False)
        self._player.video_set_mouse_input(False)

    def _attach_vlc_window(self):
        # Give VLC the *video surface* child widget, not the main window.
        # This keeps the main window's event loop intact so Qt receives all keys.
        wid = int(self._video_surface.winId())
        if sys.platform == "win32":
            self._player.set_hwnd(wid)
        elif sys.platform == "darwin":
            self._player.set_nsobject(wid)
        else:
            self._player.set_xwindow(wid)

    # ── UI setup ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        # Video surface — VLC renders here. NoFocus so it never steals keys.
        self._video_surface = QWidget(self)
        self._video_surface.setStyleSheet("background: black;")
        self._video_surface.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._video_surface.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)

        # Drawing overlay
        self._drawing = DrawingOverlay(self)
        self._drawing.hide()

        # Pinned notes — direct child of self, persists when HUD hides
        self._pinned_notes = QLabel("", self)
        self._pinned_notes.setStyleSheet(
            "color:#ffe066; background:rgba(0,0,0,185);"
            "padding:8px 14px; border-radius:5px; border:1px solid rgba(255,220,80,130);"
        )
        self._pinned_notes.setFont(QFont("Arial", 13))
        self._pinned_notes.setWordWrap(True)
        self._pinned_notes.setMaximumWidth(700)
        self._pinned_notes.hide()

        # HUD overlay (all controls sit inside this)
        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._hud.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        hud_s = "color:white; background:rgba(0,0,0,160); padding:4px 8px; border-radius:3px;"
        draw_s = (
            "color:white; background:rgba(0,0,0,160); border:none;"
            "font-size:13px; padding:4px 10px; border-radius:3px;"
            "border:1px solid rgba(255,255,255,60);"
        )

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

        # Draw toolbar buttons
        self._color_btn = QPushButton("● Color", self._hud)
        self._color_btn.setStyleSheet(f"color:{_PEN_COLORS[0]}; {draw_s}")
        self._color_btn.setFixedSize(80, 30)
        self._color_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._color_btn.clicked.connect(self._cycle_color)
        self._color_btn.hide()

        self._thin_btn = QPushButton("− Thin", self._hud)
        self._thin_btn.setStyleSheet(draw_s)
        self._thin_btn.setFixedSize(64, 30)
        self._thin_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._thin_btn.clicked.connect(self._drawing.thinner)
        self._thin_btn.hide()

        self._thick_btn = QPushButton("+ Thick", self._hud)
        self._thick_btn.setStyleSheet(draw_s)
        self._thick_btn.setFixedSize(72, 30)
        self._thick_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._thick_btn.clicked.connect(self._drawing.thicker)
        self._thick_btn.hide()

        self._clear_btn = QPushButton("✕ Clear", self._hud)
        self._clear_btn.setStyleSheet(f"color:#ff8888; {draw_s}")
        self._clear_btn.setFixedSize(72, 30)
        self._clear_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._clear_btn.clicked.connect(self._drawing.clear)
        self._clear_btn.hide()

        self._draw_hint = QLabel("", self._hud)
        self._draw_hint.setStyleSheet(
            "color:rgba(255,255,255,140); background:transparent; font-size:8pt;"
        )
        self._draw_hint.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._draw_hint.hide()

        # Playback buttons
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
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(200)
        self._poll_timer.timeout.connect(self._check_clip_end)

        self._hud_timer = QTimer(self)
        self._hud_timer.setSingleShot(True)
        self._hud_timer.setInterval(3000)
        self._hud_timer.timeout.connect(self._hide_hud)

    # ── Qt lifecycle ──────────────────────────────────────────────────────

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
        # Video surface fills the whole window
        self._video_surface.resize(self.size())
        self._drawing.resize(self.size())
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

        # Draw toolbar
        sx = (w - (80 + 64 + 72 + 72 + 36)) // 2
        sy = 10
        self._color_btn.move(sx, sy)
        self._thin_btn.move(sx + 88, sy)
        self._thick_btn.move(sx + 160, sy)
        self._clear_btn.move(sx + 240, sy)
        self._draw_hint.adjustSize()
        self._draw_hint.move((w - self._draw_hint.width()) // 2, sy + 36)

        # Pinned notes
        self._pinned_notes.setMaximumWidth(min(700, w - 24))
        self._pinned_notes.adjustSize()
        self._pinned_notes.move(12, h - 100 - self._pinned_notes.height())

    # ── Playback ──────────────────────────────────────────────────────────

    def _play_clip(self, index: int):
        if self._player is None or not self._clips or index < 0 or index >= len(self._clips):
            return
        self._current_index = index
        clip = self._clips[index]
        media = self._instance.media_new(self._video_path)
        self._player.set_media(media)
        self._player.play()
        QTimer.singleShot(300, lambda: self._seek_to(clip.start))
        self._poll_timer.start()
        self._play_btn.setText("\u23f8")
        self._update_hud_labels()
        # Reclaim keyboard focus after VLC starts
        QTimer.singleShot(400, self.setFocus)

    def _seek_to(self, t: float):
        if self._player:
            self._player.set_time(int(t * 1000))

    def _check_clip_end(self):
        if self._player is None or not self._clips:
            return
        clip = self._clips[self._current_index]
        current_time = self._player.get_time() / 1000.0
        if current_time >= clip.end:
            self._poll_timer.stop()
            if self._current_index + 1 < len(self._clips):
                QTimer.singleShot(800, lambda: self._play_clip(self._current_index + 1))
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
        notes_text = clip.notes.strip() if clip.notes else ""
        self._notes_label.setText(notes_text)
        self._pinned_notes.setText(notes_text)
        self._pinned_notes.setVisible(self._notes_pinned and bool(notes_text))
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
        self.setFocus()

    def _prev_clip(self):
        self._poll_timer.stop()
        self._play_clip(max(0, self._current_index - 1))

    def _next_clip(self):
        self._poll_timer.stop()
        self._play_clip(min(len(self._clips) - 1, self._current_index + 1))

    def _step(self, seconds: float):
        if self._player is None or not self._clips:
            return
        clip = self._clips[self._current_index]
        current = self._player.get_time() / 1000.0
        target = max(clip.start, min(clip.end - 0.1, current + seconds))
        self._seek_to(target)

    def _frame_step(self, direction: int):
        """Step one frame forward (VLC native) or back (~40 ms rewind)."""
        if self._player is None:
            return
        if self._player.is_playing():
            self._player.pause()
            self._play_btn.setText("\u25b6")
        if direction > 0:
            self._player.next_frame()
        else:
            self._step(-0.04)

    def _set_rate(self, delta: float):
        if self._player is None:
            return
        rate = max(0.25, min(4.0, self._player.get_rate() + delta))
        self._player.set_rate(rate)

    # ── HUD ───────────────────────────────────────────────────────────────

    def _hide_hud(self):
        self._hud.setVisible(False)

    def _show_hud(self):
        self._hud.setVisible(True)
        if not self._drawing_mode:
            self._hud_timer.start()

    # ── Drawing ───────────────────────────────────────────────────────────

    def _toggle_drawing(self):
        self._drawing_mode = not self._drawing_mode
        self._drawing.setVisible(self._drawing_mode)
        for w in (self._color_btn, self._thin_btn, self._thick_btn,
                  self._clear_btn, self._draw_hint):
            w.setVisible(self._drawing_mode)
        if self._drawing_mode:
            self._hud_timer.stop()
            self._drawing.raise_()
            self._hud.raise_()
            self._pinned_notes.raise_()
            self._draw_hint.setText(
                "Draw with mouse  ·  [K] cycle color  ·  [C] clear  ·  [D] exit draw mode"
            )
            self._show_hud()
        else:
            self._hud_timer.start()
        self._reposition_hud()
        self.setFocus()

    def _cycle_color(self):
        color = self._drawing.cycle_color()
        self._color_btn.setStyleSheet(
            f"color:{color.name()}; background:rgba(0,0,0,160); border:none;"
            "font-size:13px; padding:4px 10px; border-radius:3px;"
            "border:1px solid rgba(255,255,255,60);"
        )
        self.setFocus()

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
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

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
            if shift:
                self._prev_clip()
            elif not self._drawing_mode:
                self._step(-5)

        elif key == Qt.Key.Key_Right:
            if shift:
                self._next_clip()
            elif not self._drawing_mode:
                self._step(5)

        elif key in (Qt.Key.Key_Comma, Qt.Key.Key_Less):
            self._frame_step(-1)

        elif key in (Qt.Key.Key_Period, Qt.Key.Key_Greater):
            self._frame_step(1)

        elif key == Qt.Key.Key_BracketLeft:
            self._set_rate(-0.25)

        elif key == Qt.Key.Key_BracketRight:
            self._set_rate(0.25)

        elif key == Qt.Key.Key_D:
            self._toggle_drawing()

        elif key == Qt.Key.Key_C and self._drawing_mode:
            self._drawing.clear()

        elif key == Qt.Key.Key_K and self._drawing_mode:
            self._cycle_color()

        elif key == Qt.Key.Key_N:
            self._toggle_notes_pin()

        else:
            super().keyPressEvent(event)
