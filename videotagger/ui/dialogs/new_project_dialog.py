from __future__ import annotations

import os
from pathlib import Path
from typing import List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDialogButtonBox, QFileDialog,
    QListWidget, QListWidgetItem, QMessageBox, QWidget,
)

from videotagger.models.project import Project
from videotagger.data.template_manager import TemplateManager


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(520)
        self._project: Project | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ── Source files ────────────────────────────────────────────────
        layout.addWidget(QLabel("Video file(s) — add multiple for a split-file match:"))

        self._file_list = QListWidget()
        self._file_list.setMaximumHeight(120)
        layout.addWidget(self._file_list)

        file_btn_row = QHBoxLayout()
        add_btn = QPushButton("Add File(s)…")
        add_btn.clicked.connect(self._add_files)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        up_btn = QPushButton("↑")
        up_btn.setFixedWidth(32)
        up_btn.clicked.connect(self._move_up)
        down_btn = QPushButton("↓")
        down_btn.setFixedWidth(32)
        down_btn.clicked.connect(self._move_down)
        file_btn_row.addWidget(add_btn)
        file_btn_row.addWidget(remove_btn)
        file_btn_row.addStretch()
        file_btn_row.addWidget(up_btn)
        file_btn_row.addWidget(down_btn)
        layout.addLayout(file_btn_row)

        # ── Merged output location (shown only when >1 file) ────────────
        self._merge_section = QWidget()
        merge_layout = QVBoxLayout(self._merge_section)
        merge_layout.setContentsMargins(0, 0, 0, 0)
        merge_layout.addWidget(QLabel("Save merged video to:"))
        merge_row = QHBoxLayout()
        self._merge_path_edit = QLineEdit()
        self._merge_path_edit.setPlaceholderText("Path for merged output file…")
        merge_browse = QPushButton("Browse…")
        merge_browse.clicked.connect(self._browse_merge_output)
        merge_row.addWidget(self._merge_path_edit, stretch=1)
        merge_row.addWidget(merge_browse)
        merge_layout.addLayout(merge_row)
        layout.addWidget(self._merge_section)
        self._merge_section.hide()

        self._file_list.model().rowsInserted.connect(self._update_merge_section)
        self._file_list.model().rowsRemoved.connect(self._update_merge_section)

        # ── Template ────────────────────────────────────────────────────
        layout.addWidget(QLabel("Start from template (optional):"))
        self._tmpl_combo = QComboBox()
        self._tmpl_combo.addItem("— None (blank) —", None)
        for name in TemplateManager.list_builtin():
            self._tmpl_combo.addItem(f"[Built-in] {name}", ("builtin", name))
        for name in TemplateManager.list_user():
            self._tmpl_combo.addItem(f"[Custom] {name}", ("user", name))
        layout.addWidget(self._tmpl_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Video File(s)", "",
            "Video Files (*.mp4 *.mov *.avi *.mkv *.m4v);;All Files (*)",
        )
        for path in paths:
            self._file_list.addItem(QListWidgetItem(path))
        self._update_merge_default()

    def _remove_selected(self):
        for item in self._file_list.selectedItems():
            self._file_list.takeItem(self._file_list.row(item))

    def _move_up(self):
        row = self._file_list.currentRow()
        if row > 0:
            item = self._file_list.takeItem(row)
            self._file_list.insertItem(row - 1, item)
            self._file_list.setCurrentRow(row - 1)

    def _move_down(self):
        row = self._file_list.currentRow()
        if row < self._file_list.count() - 1:
            item = self._file_list.takeItem(row)
            self._file_list.insertItem(row + 1, item)
            self._file_list.setCurrentRow(row + 1)

    def _update_merge_section(self):
        self._merge_section.setVisible(self._file_list.count() > 1)

    def _update_merge_default(self):
        if self._file_list.count() > 1 and not self._merge_path_edit.text().strip():
            first = self._file_list.item(0).text()
            stem = Path(first).stem
            default = str(Path(first).parent / f"{stem}_merged.mp4")
            self._merge_path_edit.setText(default)

    def _browse_merge_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged Video As", self._merge_path_edit.text(),
            "MP4 Video (*.mp4)",
        )
        if path:
            if not path.endswith(".mp4"):
                path += ".mp4"
            self._merge_path_edit.setText(path)

    def _source_paths(self) -> List[str]:
        return [
            self._file_list.item(i).text()
            for i in range(self._file_list.count())
        ]

    def _accept(self):
        sources = self._source_paths()
        if not sources:
            QMessageBox.warning(self, "Required", "Please add at least one video file.")
            return

        for src in sources:
            if not os.path.exists(src):
                QMessageBox.warning(self, "File Not Found", f"File not found:\n{src}")
                return

        if len(sources) == 1:
            merged_path = sources[0]
        else:
            merged_path = self._merge_path_edit.text().strip()
            if not merged_path:
                QMessageBox.warning(self, "Required",
                                    "Please specify where to save the merged video.")
                return
            from videotagger.core.video_merger import VideoMerger
            from videotagger.ui.dialogs.merge_progress_dialog import MergeProgressDialog
            from videotagger.export.ffmpeg_exporter import _ffmpeg_path
            merger = VideoMerger(_ffmpeg_path())
            dlg = MergeProgressDialog(merger, sources, merged_path, self)
            if not dlg.exec() or not dlg.was_successful():
                return
            if not os.path.exists(merged_path):
                QMessageBox.critical(self, "Merge Failed",
                                     "Merged file was not created.")
                return

        tmpl_data = self._tmpl_combo.currentData()
        categories = []
        if tmpl_data:
            kind, name = tmpl_data
            categories = (TemplateManager.load_builtin(name) if kind == "builtin"
                          else TemplateManager.load_user(name))

        self._project = Project(
            source_video_paths=sources,
            merged_video_path=merged_path,
            categories=categories,
        )
        self.accept()

    def project(self) -> Project | None:
        return self._project
