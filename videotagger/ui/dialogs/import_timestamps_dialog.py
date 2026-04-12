# videotagger/ui/dialogs/import_timestamps_dialog.py
from __future__ import annotations
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QDialogButtonBox, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from videotagger.models.project import Project, Clip

# Matches: 1:23, 01:23, 1:23:45, 01:23:45  optionally followed by .ms
_TS_RE = re.compile(
    r'^(?:(\d+):)?(\d{1,2}):(\d{2})(?:\.(\d+))?\s+(.*)',
)

def parse_timestamp_line(line: str) -> tuple[float, str] | None:
    """Return (seconds, note_text) or None if line doesn't match."""
    line = line.strip()
    if not line:
        return None
    m = _TS_RE.match(line)
    if not m:
        return None
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2))
    seconds = int(m.group(3))
    ms_str = m.group(4) or "0"
    ms = int(ms_str) / (10 ** len(ms_str))
    text = m.group(5).strip()
    total = hours * 3600 + minutes * 60 + seconds + ms
    return total, text


class ImportTimestampsDialog(QDialog):
    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Timestamps")
        self.setMinimumSize(580, 480)
        self._project = project
        self._parsed: list[tuple[float, str]] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(QLabel(
            "Paste timestamps from your notes app — one per line.\n"
            "Supported formats:  4:31 Note text  ·  1:04:31 Note text"
        ))

        self._text_edit = QPlainTextEdit()
        self._text_edit.setPlaceholderText(
            "4:31 Poor decision given the game plan\n"
            "12:05 Great defensive pressure\n"
            "1:02:44 Half time review point"
        )
        self._text_edit.setFixedHeight(120)
        layout.addWidget(self._text_edit)

        # Category / label assignment
        assign_row = QHBoxLayout()
        assign_row.addWidget(QLabel("Assign to:"))
        self._cat_combo = QComboBox()
        self._lbl_combo = QComboBox()
        for cat in self._project.categories:
            self._cat_combo.addItem(cat.name, cat.id)
        self._cat_combo.currentIndexChanged.connect(self._refresh_labels)
        self._refresh_labels()
        assign_row.addWidget(self._cat_combo, stretch=1)
        assign_row.addWidget(self._lbl_combo, stretch=1)

        parse_btn = QPushButton("Preview →")
        parse_btn.clicked.connect(self._do_parse)
        assign_row.addWidget(parse_btn)
        layout.addLayout(assign_row)

        # Preview table
        layout.addWidget(QLabel("Preview (clips to be created):"))
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Time", "Note", "Status"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Import Clips")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_labels(self):
        self._lbl_combo.clear()
        cat_id = self._cat_combo.currentData()
        cat = next((c for c in self._project.categories if c.id == cat_id), None)
        if cat:
            for lbl in cat.labels:
                self._lbl_combo.addItem(lbl)

    def _fmt(self, seconds: float) -> str:
        s = int(seconds)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"

    def _do_parse(self):
        self._parsed = []
        self._table.setRowCount(0)
        lines = self._text_edit.toPlainText().splitlines()
        for line in lines:
            result = parse_timestamp_line(line)
            row = self._table.rowCount()
            self._table.insertRow(row)
            if result is None:
                self._table.setItem(row, 0, QTableWidgetItem("—"))
                self._table.setItem(row, 1, QTableWidgetItem(line or "(empty)"))
                status = QTableWidgetItem("⚠ Skipped")
                status.setForeground(Qt.GlobalColor.yellow)
                self._table.setItem(row, 2, status)
            else:
                t, note = result
                self._parsed.append((t, note))
                self._table.setItem(row, 0, QTableWidgetItem(self._fmt(t)))
                self._table.setItem(row, 1, QTableWidgetItem(note))
                status = QTableWidgetItem("✓ OK")
                status.setForeground(Qt.GlobalColor.green)
                self._table.setItem(row, 2, status)

    def _accept(self):
        if not self._parsed:
            self._do_parse()
        if not self._parsed:
            QMessageBox.warning(self, "Nothing to import",
                                "No valid timestamps were found. Check the format and try again.")
            return
        cat_id = self._cat_combo.currentData()
        label = self._lbl_combo.currentText()
        if not cat_id or not label:
            QMessageBox.warning(self, "No category selected",
                                "Please select a category and label before importing.")
            return
        self._clips = [
            Clip(category_id=cat_id, label=label,
                 start=max(0.0, t - 2.0), end=t + 8.0, notes=note)
            for t, note in self._parsed
        ]
        self.accept()

    def clips(self) -> list[Clip]:
        return getattr(self, "_clips", [])
