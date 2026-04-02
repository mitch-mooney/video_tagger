# videotagger/ui/dialogs/export_dialog.py
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QDialogButtonBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from videotagger.models.project import Project
from videotagger.core.playlist_builder import PlaylistBuilder

class ExportDialog(QDialog):
    def __init__(self, project: Project, playlist_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Playlist")
        self.setMinimumWidth(480)
        self._project = project
        self._playlist_id = playlist_id
        pl = next(p for p in project.playlists if p.id == playlist_id)
        self._clips = PlaylistBuilder(project).get_clips(playlist_id)
        self._setup_ui(pl.name)

    def _setup_ui(self, playlist_name: str):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Playlist: <b>{playlist_name}</b> ({len(self._clips)} clips)"))

        layout.addWidget(QLabel("Output folder:"))
        folder_row = QHBoxLayout()
        self._folder_edit = QLineEdit()
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse_folder)
        folder_row.addWidget(self._folder_edit, stretch=1)
        folder_row.addWidget(browse)
        layout.addLayout(folder_row)

        layout.addWidget(QLabel("Export formats:"))
        self._mp4_check = QCheckBox("Cut video files (.mp4)")
        self._mp4_check.setChecked(True)
        self._edl_check = QCheckBox("EDL reference file (.edl)")
        layout.addWidget(self._mp4_check)
        layout.addWidget(self._edl_check)

        # Naming preview
        cat_map = {c.id: c for c in self._project.categories}
        stem = Path(self._project.video_path).stem
        if self._clips:
            clip = self._clips[0]
            cat = cat_map.get(clip.category_id)
            cat_name = cat.name if cat else "Unknown"
            preview = f"{stem}_{cat_name}_{clip.label}_001.mp4"
        else:
            preview = f"{stem}_Category_Label_001.mp4"
        layout.addWidget(QLabel(f"Naming: <code>{preview}</code>"))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Export")
        buttons.accepted.connect(self._export)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self._folder_edit.setText(folder)

    def _export(self):
        folder = self._folder_edit.text().strip()
        if not folder:
            QMessageBox.warning(self, "Required", "Please select an output folder.")
            return
        do_mp4 = self._mp4_check.isChecked()
        do_edl = self._edl_check.isChecked()
        if not do_mp4 and not do_edl:
            QMessageBox.warning(self, "Required", "Select at least one export format.")
            return
        errors = []
        if do_mp4:
            from videotagger.export.ffmpeg_exporter import export_playlist_clips
            try:
                export_playlist_clips(self._clips, self._project, folder)
            except RuntimeError as e:
                errors.append(str(e))
        if do_edl:
            from videotagger.export.edl_writer import write_edl
            pl = next(p for p in self._project.playlists if p.id == self._playlist_id)
            edl_path = os.path.join(folder, f"{pl.name}.edl")
            write_edl(pl.name, self._clips, self._project, edl_path)
        if errors:
            QMessageBox.critical(self, "Export errors", "\n".join(errors))
        else:
            QMessageBox.information(self, "Done", f"Exported to:\n{folder}")
            self.accept()
