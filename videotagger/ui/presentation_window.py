# videotagger/ui/presentation_window.py
from __future__ import annotations
import sys
import math
import vlc
from enum import Enum, auto
from typing import List
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QKeyEvent, QFont, QPainter, QPen, QColor, QPixmap, QBrush
from videotagger.models.project import Clip


class DrawTool(Enum):
    PEN    = auto()
    ARROW  = auto()
    RECT   = auto()
    CIRCLE = auto()


_TOOL_COLORS = ["#ff4444", "#ffcc00", "#44aaff", "#44ff88", "#ffffff"]


class DrawingOverlay(QWidget):
    """Transparent overlay supporting freehand pen, arrow, rectangle and circle tools."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._canvas: QPixmap | None = None
        self._tool = DrawTool.PEN
        self._color_index = 0
        self._pen_color = QColor(_TOOL_COLORS[0])
        self._pen_width = 4
        # For PEN
        self._last_pos: QPoint | None = None
        # For shape tools — rubber-band preview
        self._start_pos: QPoint | None = None
        self._preview_pos: QPoint | None = None

    # ── public API ────────────────────────────────────────────────────────

    @property
    def tool(self) -> DrawTool:
        return self._tool

    def set_tool(self, tool: DrawTool):
        self._tool = tool
        self._start_pos = None
        self._preview_pos = None

    def cycle_color(self):
        self._color_index = (self._color_index + 1) % len(_TOOL_COLORS)
        self._pen_color = QColor(_TOOL_COLORS[self._color_index])

    @property
    def color(self) -> QColor:
        return self._pen_color

    def clear(self):
        if self._canvas:
            self._canvas.fill(Qt.GlobalColor.transparent)
        self._start_pos = None
        self._preview_pos = None
        self.update()

    # ── Qt events ─────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        new_canvas = QPixmap(self.size())
        new_canvas.fill(Qt.GlobalColor.transparent)
        if self._canvas:
            painter = QPainter(new_canvas)
            painter.drawPixmap(0, 0, self._canvas)
            painter.end()
        self._canvas = new_canvas
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._canvas:
            painter.drawPixmap(0, 0, self._canvas)
        # Rubber-band preview for shape tools
        if self._start_pos and self._preview_pos and self._tool != DrawTool.PEN:
            pen = QPen(self._pen_color, self._pen_width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            self._draw_shape(painter, self._tool, self._start_pos, self._preview_pos)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position().toPoint()
        if self._tool == DrawTool.PEN:
            self._last_pos = pos
        else:
            self._start_pos = pos
            self._preview_pos = pos

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        pos = event.position().toPoint()
        if self._tool == DrawTool.PEN:
            if self._last_pos is not None:
                self._ensure_canvas()
                painter = QPainter(self._canvas)
                pen = QPen(self._pen_color, self._pen_width, Qt.PenStyle.SolidLine,
                           Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(self._last_pos, pos)
                painter.end()
                self._last_pos = pos
        else:
            self._preview_pos = pos
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position().toPoint()
        if self._tool == DrawTool.PEN:
            self._last_pos = None
        elif self._start_pos is not None:
            self._ensure_canvas()
            painter = QPainter(self._canvas)
            pen = QPen(self._pen_color, self._pen_width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            self._draw_shape(painter, self._tool, self._start_pos, pos)
            painter.end()
            self._start_pos = None
            self._preview_pos = None
            self.update()

    # ── helpers ───────────────────────────────────────────────────────────

    def _ensure_canvas(self):
        if self._canvas is None:
            self._canvas = QPixmap(self.size())
            self._canvas.fill(Qt.GlobalColor.transparent)

    @staticmethod
    def _draw_shape(painter: QPainter, tool: DrawTool, p1: QPoint, p2: QPoint):
        if tool == DrawTool.RECT:
            painter.drawRect(QRect(p1, p2).normalized())
        elif tool == DrawTool.CIRCLE:
            painter.drawEllipse(QRect(p1, p2).normalized())
        elif tool == DrawTool.ARROW:
            painter.drawLine(p1, p2)
            # Arrowhead
            dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
            length = math.hypot(dx, dy)
            if length < 1:
                return
            ux, uy = dx / length, dy / length
            head = 18
            spread = 0.4
            lx = p2.x() - head * (ux + spread * uy)
            ly = p2.y() - head * (uy - spread * ux)
            rx = p2.x() - head * (ux - spread * uy)
            ry = p2.y() - head * (uy + spread * ux)
            painter.drawLine(p2, QPoint(int(lx), int(ly)))
            painter.drawLine(p2, QPoint(int(rx), int(ry)))


class AnnotationToolbar(QWidget):
    """Small tool-selector strip shown at top-centre when draw mode is active."""

    tool_selected = pyqtSignal(object)   # DrawTool
    color_cycled  = pyqtSignal()
    clear_clicked = pyqtSignal()

    _TOOLS = [
        (DrawTool.PEN,    "✏",  "Pen (1)"),
        (DrawTool.ARROW,  "↗",  "Arrow (2)"),
        (DrawTool.RECT,   "▭",  "Rect (3)"),
        (DrawTool.CIRCLE, "○",  "Circle (4)"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        btn_base = (
            "border-radius:4px; padding:4px 10px; font-size:13px; font-weight:600;"
            "border:1px solid rgba(255,255,255,60);"
        )
        self._tool_btns: dict[DrawTool, QPushButton] = {}
        for tool, icon, tip in self._TOOLS:
            btn = QPushButton(icon)
            btn.setToolTip(tip)
            btn.setFixedSize(38, 32)
            btn.setStyleSheet(f"color:white; background:rgba(0,0,0,160); {btn_base}")
            btn.clicked.connect(lambda checked, t=tool: self.tool_selected.emit(t))
            layout.addWidget(btn)
            self._tool_btns[tool] = btn

        layout.addSpacing(8)

        self._color_btn = QPushButton("●")
        self._color_btn.setFixedSize(38, 32)
        self._color_btn.setStyleSheet(
            f"color:#ff4444; background:rgba(0,0,0,160); {btn_base}"
        )
        self._color_btn.setToolTip("Cycle color (K)")
        self._color_btn.clicked.connect(self.color_cycled.emit)
        layout.addWidget(self._color_btn)

        clr_btn = QPushButton("✕ Clear")
        clr_btn.setFixedSize(68, 32)
        clr_btn.setStyleSheet(f"color:#ff6666; background:rgba(0,0,0,160); {btn_base}")
        clr_btn.setToolTip("Clear all (C)")
        clr_btn.clicked.connect(self.clear_clicked.emit)
        layout.addWidget(clr_btn)

        self.adjustSize()
        self.hide()

    def highlight_tool(self, tool: DrawTool):
        for t, btn in self._tool_btns.items():
            active = t == tool
            btn.setStyleSheet(
                f"color:{'#00ffcc' if active else 'white'};"
                f"background:{'rgba(0,80,60,200)' if active else 'rgba(0,0,0,160)'};"
                f"border-radius:4px; padding:4px 10px; font-size:13px; font-weight:600;"
                f"border:1px solid {'#00ffcc' if active else 'rgba(255,255,255,60)'};"
            )

    def update_color(self, color: QColor):
        self._color_btn.setStyleSheet(
            f"color:{color.name()}; background:rgba(0,0,0,160);"
            "border-radius:4px; padding:4px 10px; font-size:13px; font-weight:600;"
            "border:1px solid rgba(255,255,255,60);"
        )


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
        self._drawing_mode = False
        self._notes_pinned = False
        self._setup_ui()
        self._setup_timers()

    # ── VLC init ──────────────────────────────────────────────────────────

    def _init_vlc(self):
        if self._instance is not None:
            return
        args = ["--no-plugins-cache"]
        if sys.platform == "linux":
            args.append("--no-xlib")
        self._instance = vlc.Instance(*args)
        self._player = self._instance.media_player_new()

    def _attach_vlc_window(self):
        if sys.platform == "win32":
            self._player.set_hwnd(int(self.winId()))
        elif sys.platform == "darwin":
            self._player.set_nsobject(int(self.winId()))
        else:
            self._player.set_xwindow(int(self.winId()))

    # ── UI setup ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        # Drawing overlay — sits behind HUD
        self._drawing = DrawingOverlay(self)
        self._drawing.hide()

        # Annotation toolbar — child of self so it's above drawing but controllable
        self._ann_toolbar = AnnotationToolbar(self)
        self._ann_toolbar.tool_selected.connect(self._on_tool_selected)
        self._ann_toolbar.color_cycled.connect(self._on_color_cycled)
        self._ann_toolbar.clear_clicked.connect(self._drawing.clear)

        # Pinned notes label — direct child of self so it survives HUD hide
        self._pinned_notes = QLabel("", self)
        self._pinned_notes.setStyleSheet(
            "color:#ffe066; background:rgba(0,0,0,180);"
            "padding:6px 12px; border-radius:4px; border:1px solid rgba(255,220,80,120);"
        )
        self._pinned_notes.setFont(QFont("Arial", 13))
        self._pinned_notes.setWordWrap(True)
        self._pinned_notes.setMaximumWidth(700)
        self._pinned_notes.hide()

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

        # Inline notes (hidden when pinned notes are showing)
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

        # Notes-pin hint (shown bottom-right alongside counter)
        self._notes_hint = QLabel("[N] pin notes", self._hud)
        self._notes_hint.setStyleSheet(
            "color: rgba(255,255,255,100); background: transparent; font-size: 8pt;"
        )
        self._notes_hint.setFont(QFont("Arial", 8))

        btn_style = (
            "color: white; background: rgba(0,0,0,160); border: none;"
            "font-size: 20px; padding: 6px 12px; border-radius: 3px;"
        )
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

        self._notes_label.adjustSize()
        notes_visible = bool(self._notes_label.text()) and not self._notes_pinned
        self._notes_label.setVisible(notes_visible)
        self._notes_label.move(12, h - 50)

        self._counter_label.adjustSize()
        self._counter_label.move(w - self._counter_label.width() - 12, h - 72)

        self._notes_hint.adjustSize()
        self._notes_hint.move(w - self._notes_hint.width() - 12, h - 52)

        cx = (w - 160) // 2
        self._prev_btn.move(cx, h - 52)
        self._play_btn.move(cx + 55, h - 52)
        self._next_btn.move(cx + 110, h - 52)

        # Annotation toolbar — centred at top
        self._ann_toolbar.adjustSize()
        self._ann_toolbar.move((w - self._ann_toolbar.width()) // 2, 8)

        # Pinned notes — bottom-left, above clip label
        self._pinned_notes.setMaximumWidth(min(700, w - 24))
        self._pinned_notes.adjustSize()
        self._pinned_notes.move(12, h - 90 - self._pinned_notes.height())

    # ── Playback ──────────────────────────────────────────────────────────

    def _play_clip(self, index: int):
        if self._player is None or not self._clips or index < 0 or index >= len(self._clips):
            return
        self._current_index = index
        clip = self._clips[index]
        media = self._instance.media_new(self._video_path)
        self._player.set_media(media)
        self._player.play()
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
        target = max(clip.start, min(clip.end, current + seconds))
        self._player.set_time(int(target * 1000))

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
        self._hud_timer.start()

    # ── Drawing mode ──────────────────────────────────────────────────────

    def _toggle_drawing(self):
        self._drawing_mode = not self._drawing_mode
        self._drawing.setVisible(self._drawing_mode)
        self._ann_toolbar.setVisible(self._drawing_mode)
        if self._drawing_mode:
            self._drawing.raise_()
            self._ann_toolbar.raise_()
            self._hud.raise_()
            self._ann_toolbar.highlight_tool(self._drawing.tool)
            self._show_hud()
        else:
            self._hud_timer.start()
        self._reposition_hud()

    def _on_tool_selected(self, tool: DrawTool):
        self._drawing.set_tool(tool)
        self._ann_toolbar.highlight_tool(tool)

    def _on_color_cycled(self):
        self._drawing.cycle_color()
        self._ann_toolbar.update_color(self._drawing.color)

    # ── Notes pin ─────────────────────────────────────────────────────────

    def _toggle_notes_pin(self):
        self._notes_pinned = not self._notes_pinned
        notes_text = self._notes_label.text()
        self._pinned_notes.setVisible(self._notes_pinned and bool(notes_text))
        if self._notes_pinned:
            self._pinned_notes.raise_()
        hint = "[N] unpin notes" if self._notes_pinned else "[N] pin notes"
        self._notes_hint.setText(hint)
        self._reposition_hud()
        self._show_hud()

    # ── Mouse / keyboard ──────────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        if not self._drawing_mode:
            self._show_hud()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        mods = event.modifiers()
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)

        if key in (Qt.Key.Key_Escape, Qt.Key.Key_F11):
            self._poll_timer.stop()
            self._hud_timer.stop()
            if self._player is not None:
                self._player.stop()
            self.closed.emit()
            self.close()
        elif key == Qt.Key.Key_D:
            self._toggle_drawing()
        elif key == Qt.Key.Key_N:
            self._toggle_notes_pin()
        elif key == Qt.Key.Key_C and self._drawing_mode:
            self._drawing.clear()
        elif key == Qt.Key.Key_K and self._drawing_mode:
            self._on_color_cycled()
        elif key == Qt.Key.Key_1 and self._drawing_mode:
            self._on_tool_selected(DrawTool.PEN)
        elif key == Qt.Key.Key_2 and self._drawing_mode:
            self._on_tool_selected(DrawTool.ARROW)
        elif key == Qt.Key.Key_3 and self._drawing_mode:
            self._on_tool_selected(DrawTool.RECT)
        elif key == Qt.Key.Key_4 and self._drawing_mode:
            self._on_tool_selected(DrawTool.CIRCLE)
        elif key == Qt.Key.Key_Space:
            self._toggle_play()
        elif key == Qt.Key.Key_Left and not self._drawing_mode:
            if shift:
                self._prev_clip()
            else:
                self._step(-5)
        elif key == Qt.Key.Key_Right and not self._drawing_mode:
            if shift:
                self._next_clip()
            else:
                self._step(5)
        elif key == Qt.Key.Key_BracketLeft:
            self._set_rate(-0.25)
        elif key == Qt.Key.Key_BracketRight:
            self._set_rate(0.25)
        else:
            super().keyPressEvent(event)
