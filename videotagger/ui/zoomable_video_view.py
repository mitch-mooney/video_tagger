# videotagger/ui/zoomable_video_view.py
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, QSizeF, Qt
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtWidgets import QFrame, QGraphicsScene, QGraphicsView

from videotagger.ui.zoom_geometry import clamp_zoom, visible_rect

_ZOOM_STEP = 1.25


class ZoomableVideoView(QGraphicsView):
    """A video surface that supports zoom (wheel / +/- / API) and pan (drag).

    Pass `view.video_item` to `QMediaPlayer.setVideoOutput()`. Zoom factor 1.0
    means the whole frame is visible (fit); higher means zoomed in.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._video_item = QGraphicsVideoItem()
        self._scene.addItem(self._video_item)

        self._zoom = 1.0
        self._center = QPointF(0.0, 0.0)
        self._pan_last = None

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background: black; border: none;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._video_item.nativeSizeChanged.connect(self._on_native_size)

    # -- Public API --

    @property
    def video_item(self) -> QGraphicsVideoItem:
        return self._video_item

    @property
    def is_zoomed(self) -> bool:
        return self._zoom > 1.0 + 1e-6

    def zoom_in(self, factor: float = _ZOOM_STEP) -> None:
        self._set_zoom(self._zoom * factor)

    def zoom_out(self, factor: float = _ZOOM_STEP) -> None:
        self._set_zoom(self._zoom / factor)

    def reset_zoom(self) -> None:
        self._zoom = 1.0
        self._center = self._frame_center()
        self._update_view()

    # -- Internal --

    def _frame_size(self) -> QSizeF:
        return self._video_item.size()

    def _frame_center(self) -> QPointF:
        s = self._frame_size()
        return QPointF(s.width() / 2.0, s.height() / 2.0)

    def _set_zoom(self, zoom: float) -> None:
        self._zoom = clamp_zoom(zoom)
        self._update_view()

    def _on_native_size(self, size: QSizeF) -> None:
        if size.isEmpty():
            return
        self._video_item.setSize(size)
        self._scene.setSceneRect(self._video_item.boundingRect())
        self._center = self._frame_center()
        self._update_view()

    def _update_view(self) -> None:
        s = self._frame_size()
        if s.width() <= 0 or s.height() <= 0:
            return
        x, y, w, h = visible_rect(
            self._center.x(), self._center.y(), s.width(), s.height(), self._zoom
        )
        self._center = QPointF(x + w / 2.0, y + h / 2.0)
        self.fitInView(QRectF(x, y, w, h), Qt.AspectRatioMode.KeepAspectRatio)

    # -- Events --

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_view()

    def wheelEvent(self, event):
        s = self._frame_size()
        if s.width() <= 0:
            return
        event.accept()
        old = self._zoom
        factor = _ZOOM_STEP if event.angleDelta().y() > 0 else 1.0 / _ZOOM_STEP
        new = clamp_zoom(old * factor)
        if new == old:
            return
        # Keep the frame point under the cursor anchored. mapToScene/mapFromScene
        # account for the actual fitted transform (including letterbox bars), so
        # this stays correct regardless of the view's aspect ratio.
        pos = event.position().toPoint()
        scene_before = self.mapToScene(pos)
        self._zoom = new
        self._update_view()
        scene_after = self.mapToScene(pos)
        self._center = QPointF(
            self._center.x() + (scene_before.x() - scene_after.x()),
            self._center.y() + (scene_before.y() - scene_after.y()),
        )
        self._update_view()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_zoomed:
            self._pan_last = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_last is not None:
            # Derive scene-units-per-pixel from the actual fitted scale (m11 == m22
            # under KeepAspectRatio), which is letterbox-correct on any aspect ratio.
            scale = self.transform().m11()
            scene_per_px = 1.0 / scale if scale else 0.0
            d = event.position() - self._pan_last
            self._center = QPointF(
                self._center.x() - d.x() * scene_per_px,
                self._center.y() - d.y() * scene_per_px,
            )
            self._pan_last = event.position()
            self._update_view()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._pan_last is not None:
            self._pan_last = None
            self.unsetCursor()
        super().mouseReleaseEvent(event)
