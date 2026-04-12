# videotagger/ui/timeline_widget.py
from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QToolTip
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from videotagger.models.project import Project

class TimelineWidget(QWidget):
    seek_requested = pyqtSignal(float)
    clip_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project: Project | None = None
        self._duration = 0.0
        self._position = 0.0
        self._filter: str = ""
        self.setMinimumHeight(50)
        self.setMouseTracking(True)

    def set_project(self, project: Project) -> None:
        self._project = project
        self.update()

    def set_duration(self, seconds: float) -> None:
        self._duration = seconds
        self.update()

    def set_position(self, seconds: float) -> None:
        self._position = seconds
        self.update()

    def set_filter(self, text: str) -> None:
        self._filter = text.lower().strip()
        self.update()

    def _clip_matches(self, clip, cat_map: dict) -> bool:
        if not self._filter:
            return True
        cat = cat_map.get(clip.category_id)
        searchable = " ".join([
            clip.label, clip.notes, cat.name if cat else ""
        ]).lower()
        return self._filter in searchable

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor("#1a1a2e"))

        if self._duration <= 0 or not self._project:
            painter.end()
            return

        track_y = h // 2 - 6
        track_h = 12
        painter.fillRect(0, track_y, w, track_h, QColor("#0f3460"))

        cat_map = {c.id: c for c in self._project.categories}
        for clip in self._project.clips:
            x1 = int(clip.start / self._duration * w)
            x2 = int(clip.end / self._duration * w)
            cat = cat_map.get(clip.category_id)
            color = QColor(cat.color if cat else "#888888")

            matches = self._clip_matches(clip, cat_map)
            if self._filter and not matches:
                color.setAlphaF(0.2)  # dim non-matching clips

            painter.fillRect(x1, track_y, max(2, x2 - x1), track_h, color)

            # Draw a small dot above clip if it has notes
            if clip.notes and clip.notes.strip():
                dot_x = x1 + max(1, (x2 - x1) // 2)
                dot_color = QColor("#ffffff") if matches or not self._filter else QColor("#555555")
                painter.setBrush(dot_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(dot_x - 2, track_y - 5, 4, 4)

        # Playhead
        px = int(self._position / self._duration * w)
        pen = QPen(QColor("white"), 2)
        painter.setPen(pen)
        painter.drawLine(px, 0, px, h)

        painter.end()

    def mouseMoveEvent(self, event):
        if self._duration <= 0 or not self._project:
            return
        x = event.position().x()
        cat_map = {c.id: c for c in self._project.categories}
        for clip in self._project.clips:
            x1 = clip.start / self._duration * self.width()
            x2 = clip.end / self._duration * self.width()
            if x1 <= x <= x2:
                cat = cat_map.get(clip.category_id)
                cat_name = cat.name if cat else ""
                tip = f"{cat_name} — {clip.label}" if cat_name else clip.label
                if clip.notes and clip.notes.strip():
                    tip += f"\n{clip.notes}"
                QToolTip.showText(event.globalPosition().toPoint(), tip, self)
                return
        QToolTip.hideText()

    def mousePressEvent(self, event):
        if self._duration <= 0:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            if self._project:
                for clip in self._project.clips:
                    x1 = clip.start / self._duration * self.width()
                    x2 = clip.end / self._duration * self.width()
                    if x1 <= x <= x2:
                        self.clip_clicked.emit(clip.id)
                        return
            t = x / self.width() * self._duration
            self.seek_requested.emit(t)
