"""Mark where each match period (quarter/half) begins on the primary timeline.

Periods drive the Q1–Q4 dividers on the timeline ribbon (and the per-period sync
points used by the dual-angle feature). This dialog is independent of angle sync —
it works on any single-angle project. The scrubbable preview and time helpers are
shared with the angle-sync dialog.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from videotagger.core.angle_sync import PeriodMark, build_periods
from videotagger.ui.dialogs.angle_sync_dialog import _Preview, _fmt_precise


class ManagePeriodsDialog(QDialog):
    """Capture each period's start time on the primary video and save to the project."""

    _START_COL = 1

    def __init__(self, doc, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Periods")
        self.setMinimumSize(560, 540)
        self._doc = doc
        self._project = doc.project
        self._setup_ui()
        self._load_preview()
        self._populate()

    # ── UI ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(QLabel(
            "Scrub the video to the frame each period begins, then capture it. "
            "Periods draw the dividers on the timeline."))

        self._preview = _Preview("Primary video")
        layout.addWidget(self._preview, stretch=1)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Period", "Start"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setColumnWidth(0, 220)
        layout.addWidget(self._table)

        row = QHBoxLayout()
        add_p = QPushButton("Add Period")
        add_p.clicked.connect(lambda: self._add_row(f"P{self._table.rowCount() + 1}"))
        rm_p = QPushButton("Remove Period")
        rm_p.clicked.connect(self._remove_row)
        set_start = QPushButton("Set Start @ Playhead")
        set_start.clicked.connect(self._capture)
        row.addWidget(add_p)
        row.addWidget(rm_p)
        row.addStretch()
        row.addWidget(set_start)
        layout.addLayout(row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ── Preview / rows ──────────────────────────────────────────────────

    def _load_preview(self):
        if self._project.merged_video_path:
            self._preview.load(self._project.merged_video_path)

    def _populate(self):
        if self._project.periods:
            for period in self._project.periods:
                self._add_row(period.name, start=period.primary_start, period_id=period.id)
        else:
            for name in ("Q1", "Q2", "Q3", "Q4"):
                self._add_row(name)

    def _add_row(self, name: str, start=None, period_id=None):
        row = self._table.rowCount()
        self._table.insertRow(row)
        name_item = QTableWidgetItem(name)
        if period_id:
            name_item.setData(Qt.ItemDataRole.UserRole, period_id)
        self._table.setItem(row, 0, name_item)
        self._table.setItem(row, self._START_COL, self._time_item(start))

    def _remove_row(self):
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

    def _cell_time(self, row: int) -> Optional[float]:
        item = self._table.item(row, self._START_COL)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _capture(self):
        row = self._table.currentRow()
        if row < 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Select a period",
                                    "Select a period row first, then capture.")
            return
        self._table.setItem(row, self._START_COL, self._time_item(self._preview.position()))

    # ── Accept ──────────────────────────────────────────────────────────

    def _accept(self):
        marks = [
            PeriodMark(
                name=self._table.item(row, 0).text(),
                primary_start=self._cell_time(row),
                period_id=self._table.item(row, 0).data(Qt.ItemDataRole.UserRole),
            )
            for row in range(self._table.rowCount())
        ]
        self._doc.set_periods(build_periods(marks))
        self.accept()

    def done(self, result):
        self._preview.stop()
        super().done(result)
