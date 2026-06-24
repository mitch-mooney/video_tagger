from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSlider,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from videotagger.core.angle_sync import (
    PeriodMark, build_angle, duplicate_anchor_periods, unsynced_periods,
    valid_angle_starts,
)

_FRAME = 0.04  # ≈ one frame at 25fps, matches the main-window frame step


def _fmt_precise(seconds: float) -> str:
    s = max(0.0, seconds)
    m = int(s // 60)
    return f"{m:02d}:{s - m * 60:05.2f}"


class _Preview(QWidget):
    """A minimal scrubbable video preview used to find period start frames."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._duration = 0.0
        self._pending_pause = False
        self._player = QMediaPlayer(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        layout.addWidget(QLabel(title))
        self._video = QVideoWidget()
        self._video.setMinimumSize(320, 180)
        self._player.setVideoOutput(self._video)
        layout.addWidget(self._video, stretch=1)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 10000)
        self._slider.sliderMoved.connect(self._seek_to_slider)
        layout.addWidget(self._slider)

        row = QHBoxLayout()
        for text, delta in (("⏮ -1f", -_FRAME), ("⏯", None), ("+1f ⏭", _FRAME)):
            btn = QPushButton(text)
            btn.setFixedWidth(64)
            if delta is None:
                btn.clicked.connect(self._toggle)
            else:
                btn.clicked.connect(lambda _=False, d=delta: self._step(d))
            row.addWidget(btn)
        self._time_label = QLabel("00:00.00")
        row.addWidget(self._time_label)
        row.addStretch()
        layout.addLayout(row)

        self._player.positionChanged.connect(self._on_position)
        self._player.durationChanged.connect(self._on_duration)
        self._player.mediaStatusChanged.connect(self._on_media_status)

    def load(self, path: str) -> None:
        # Play briefly so the first frame decodes and renders, then hold on it.
        # Pausing before the media has loaded leaves the surface blank on Windows.
        self._player.setSource(QUrl.fromLocalFile(path))
        self._pending_pause = True
        self._player.play()

    def _on_media_status(self, status) -> None:
        if self._pending_pause and status in (
            QMediaPlayer.MediaStatus.LoadedMedia,
            QMediaPlayer.MediaStatus.BufferedMedia,
        ):
            self._pending_pause = False
            self._player.pause()

    def position(self) -> float:
        return self._player.position() / 1000.0

    def stop(self) -> None:
        self._player.stop()

    def _toggle(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _step(self, delta: float) -> None:
        self._player.pause()
        self._player.setPosition(int(max(0.0, self.position() + delta) * 1000))

    def _seek_to_slider(self, value: int) -> None:
        if self._duration > 0:
            self._player.setPosition(int(value / 10000.0 * self._duration * 1000))

    def _on_position(self, ms: int) -> None:
        pos = ms / 1000.0
        self._time_label.setText(_fmt_precise(pos))
        if self._duration > 0:
            was = self._slider.blockSignals(True)
            self._slider.setValue(int(pos / self._duration * 10000))
            self._slider.blockSignals(was)

    def _on_duration(self, ms: int) -> None:
        self._duration = ms / 1000.0


class AngleSyncDialog(QDialog):
    """Add/edit a second camera angle and mark where each period starts in both videos."""

    _PRIMARY_COL, _SECONDARY_COL = 1, 2

    def __init__(self, doc, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Angles")
        self.setMinimumSize(760, 620)
        self._doc = doc
        self._project = doc.project
        self._existing = self._project.angles[0] if self._project.angles else None
        self._secondary_merged: Optional[str] = (
            self._existing.merged_video_path if self._existing else None
        )
        self._secondary_sources: List[str] = (
            list(self._existing.source_video_paths) if self._existing else []
        )
        self._primary_swapped = False
        self._setup_ui()
        self._load_previews()
        self._populate_periods()

    # ── UI ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Secondary angle name + source files.
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Second angle name:"))
        self._name_edit = QLineEdit(self._existing.name if self._existing else "Broadcast")
        name_row.addWidget(self._name_edit, stretch=1)
        layout.addLayout(name_row)

        layout.addWidget(QLabel("Second angle video file(s) — add multiple for a split-file angle:"))
        self._file_list = QListWidget()
        self._file_list.setMaximumHeight(80)
        for src in self._secondary_sources:
            self._file_list.addItem(QListWidgetItem(src))
        layout.addWidget(self._file_list)

        file_row = QHBoxLayout()
        add_btn = QPushButton("Add File(s)…")
        add_btn.clicked.connect(self._add_files)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        self._load_btn = QPushButton("Load / Merge Angle")
        self._load_btn.clicked.connect(self._load_secondary)
        file_row.addWidget(add_btn)
        file_row.addWidget(remove_btn)
        file_row.addStretch()
        file_row.addWidget(self._load_btn)
        layout.addLayout(file_row)

        # Side-by-side previews.
        previews = QHBoxLayout()
        self._primary_preview = _Preview("Primary (existing) angle")
        self._secondary_preview = _Preview("Second angle")
        previews.addWidget(self._primary_preview)
        previews.addWidget(self._secondary_preview)
        layout.addLayout(previews, stretch=1)

        # Period table.
        layout.addWidget(QLabel(
            "Scrub each video to the frame a period begins, then capture it:"))
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Period", "Primary start", "Second-angle start"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setColumnWidth(0, 160)
        self._table.setColumnWidth(1, 180)
        layout.addWidget(self._table)

        cap_row = QHBoxLayout()
        add_p = QPushButton("Add Period")
        add_p.clicked.connect(lambda: self._add_period_row(f"P{self._table.rowCount() + 1}"))
        rm_p = QPushButton("Remove Period")
        rm_p.clicked.connect(self._remove_period_row)
        set_primary = QPushButton("Set Primary @ Playhead")
        set_primary.clicked.connect(lambda: self._capture(self._PRIMARY_COL, self._primary_preview))
        set_secondary = QPushButton("Set Second @ Playhead")
        set_secondary.clicked.connect(lambda: self._capture(self._SECONDARY_COL, self._secondary_preview))
        clear_secondary = QPushButton("Clear Second")
        clear_secondary.setToolTip(
            "Clear the second-angle start for the selected period — use this for quarters "
            "this angle didn't record, so it's left blank rather than 0:00.")
        clear_secondary.clicked.connect(lambda: self._clear(self._SECONDARY_COL))
        cap_row.addWidget(add_p)
        cap_row.addWidget(rm_p)
        cap_row.addStretch()
        cap_row.addWidget(set_primary)
        cap_row.addWidget(set_secondary)
        cap_row.addWidget(clear_secondary)
        layout.addLayout(cap_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        make_primary_btn = buttons.addButton(
            "Make This Angle Primary", QDialogButtonBox.ButtonRole.ActionRole
        )
        make_primary_btn.clicked.connect(self._make_primary)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ── Source files / merge ────────────────────────────────────────────

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Video File(s)", "",
            "Video Files (*.mp4 *.mov *.avi *.mkv *.m4v);;All Files (*)",
        )
        for path in paths:
            self._file_list.addItem(QListWidgetItem(path))

    def _remove_selected(self):
        for item in self._file_list.selectedItems():
            self._file_list.takeItem(self._file_list.row(item))

    def _source_paths(self) -> List[str]:
        return [self._file_list.item(i).text() for i in range(self._file_list.count())]

    def _load_secondary(self):
        sources = self._source_paths()
        if not sources:
            QMessageBox.warning(self, "Required", "Add at least one video file for the angle.")
            return
        for src in sources:
            if not os.path.exists(src):
                QMessageBox.warning(self, "File Not Found", f"File not found:\n{src}")
                return

        if len(sources) == 1:
            merged = sources[0]
        else:
            stem = Path(sources[0]).stem
            merged = str(Path(sources[0]).parent / f"{stem}_angle_merged.mp4")
            from videotagger.core.video_merger import VideoMerger
            from videotagger.ui.dialogs.merge_progress_dialog import MergeProgressDialog
            from videotagger.export.ffmpeg_exporter import _ffmpeg_path
            merger = VideoMerger(_ffmpeg_path())
            dlg = MergeProgressDialog(merger, sources, merged, self)
            if not dlg.exec() or not dlg.was_successful() or not os.path.exists(merged):
                return

        self._secondary_sources = sources
        self._secondary_merged = merged
        self._secondary_preview.load(merged)

    # ── Previews / periods ──────────────────────────────────────────────

    def _load_previews(self):
        if self._project.merged_video_path:
            self._primary_preview.load(self._project.merged_video_path)
        if self._secondary_merged:
            self._secondary_preview.load(self._secondary_merged)

    def _populate_periods(self):
        existing = self._project.periods
        # Show out-of-order (phantom 0:00) sync points as blank, not 0:00.
        starts = valid_angle_starts(existing, self._existing) if self._existing else {}
        if existing:
            for period in existing:
                self._add_period_row(
                    period.name,
                    primary=period.primary_start,
                    secondary=starts.get(period.id),
                    period_id=period.id,
                )
        else:
            for name in ("Q1", "Q2", "Q3", "Q4"):
                self._add_period_row(name)

    def _add_period_row(self, name: str, primary=None, secondary=None, period_id=None):
        row = self._table.rowCount()
        self._table.insertRow(row)
        name_item = QTableWidgetItem(name)
        if period_id:
            name_item.setData(Qt.ItemDataRole.UserRole, period_id)
        self._table.setItem(row, 0, name_item)
        self._table.setItem(row, self._PRIMARY_COL, self._time_item(primary))
        self._table.setItem(row, self._SECONDARY_COL, self._time_item(secondary))

    def _remove_period_row(self):
        row = self._table.currentRow()
        if row >= 0:
            self._table.removeRow(row)

    @staticmethod
    def _time_item(value: Optional[float]) -> QTableWidgetItem:
        item = QTableWidgetItem("—" if value is None else _fmt_precise(value))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if value is not None:
            item.setData(Qt.ItemDataRole.UserRole, float(value))
        return item

    def _capture(self, col: int, preview: _Preview):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select a period",
                                    "Select a period row first, then capture.")
            return
        self._table.setItem(row, col, self._time_item(preview.position()))

    def _clear(self, col: int):
        """Clear a captured time back to blank (null) for the selected period."""
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select a period",
                                    "Select a period row first, then clear.")
            return
        self._table.setItem(row, col, self._time_item(None))

    # ── Accept ──────────────────────────────────────────────────────────

    def _cell_time(self, row: int, col: int) -> Optional[float]:
        item = self._table.item(row, col)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _collect(self):
        """Build (periods, angle) from the table, or None if no second angle loaded."""
        if not self._secondary_merged:
            QMessageBox.warning(self, "Required",
                                "Load the second angle video before saving.")
            return None
        marks = [
            PeriodMark(
                name=self._table.item(row, 0).text(),
                primary_start=self._cell_time(row, self._PRIMARY_COL),
                secondary_start=self._cell_time(row, self._SECONDARY_COL),
                period_id=self._table.item(row, 0).data(Qt.ItemDataRole.UserRole),
            )
            for row in range(self._table.rowCount())
        ]
        return build_angle(
            marks,
            name=self._name_edit.text(),
            source_paths=self._secondary_sources,
            merged_path=self._secondary_merged,
            existing_angle_id=self._existing.id if self._existing else None,
        )

    def _accept(self):
        collected = self._collect()
        if collected is None:
            return
        self._doc.set_secondary_angle(*collected)
        self.accept()

    def _make_primary(self):
        """Promote this second angle to the primary (canonical) timeline."""
        collected = self._collect()
        if collected is None:
            return
        periods, angle = collected
        if not periods:
            QMessageBox.warning(self, "No periods",
                                "Mark at least one period start before making this primary.")
            return
        dups = duplicate_anchor_periods(periods)
        if dups:
            names = ", ".join(p.name for p in dups)
            QMessageBox.warning(
                self, "Duplicate period starts",
                "Two or more periods start at the same time (often 0:00 from periods that "
                "were never marked). Give each a distinct Primary start, or remove the extras, "
                "before making this primary — otherwise clips get remapped to the wrong period.\n\n"
                f"Duplicated: {names}")
            return
        missing = unsynced_periods(periods, angle)
        if missing:
            names = ", ".join(p.name for p in missing)
            QMessageBox.warning(
                self, "Unsynced periods",
                "Mark the second-angle start for every period before making it primary.\n\n"
                f"Missing: {names}")
            return
        # Save the angle (with the sync points just entered) so the swap uses them.
        self._doc.set_secondary_angle(periods, angle)
        n_clips = len(self._doc.project.clips)
        reply = QMessageBox.question(
            self, "Make Primary",
            f"Make “{angle.name or 'this angle'}” the primary video?\n\n"
            f"• Re-anchors {len(periods)} period(s) to the new timeline\n"
            f"• Remaps {n_clips} clip(s)\n"
            f"• Current video becomes the secondary angle “Original”",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok,
        )
        if reply != QMessageBox.StandardButton.Ok:
            return
        self._doc.promote_secondary_to_primary("Original")
        self._primary_swapped = True
        self.accept()

    def done(self, result):
        self._primary_preview.stop()
        self._secondary_preview.stop()
        super().done(result)
