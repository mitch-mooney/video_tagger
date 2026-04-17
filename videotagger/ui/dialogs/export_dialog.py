import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QDialogButtonBox, QFileDialog, QMessageBox, QProgressDialog,
    QGroupBox,
)
from PyQt6.QtCore import Qt
from videotagger.models.project import Project
from videotagger.core.playlist_builder import PlaylistBuilder


class ExportDialog(QDialog):
    def __init__(self, project: Project, playlist_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Playlist")
        self.setMinimumWidth(500)
        self._project = project
        self._playlist_id = playlist_id
        self._pl = next(p for p in project.playlists if p.id == playlist_id)
        self._clips = PlaylistBuilder(project).get_clips(playlist_id)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            f"Playlist: <b>{self._pl.name}</b> ({len(self._clips)} clips)"
        ))

        layout.addWidget(QLabel("Output folder:"))
        folder_row = QHBoxLayout()
        self._folder_edit = QLineEdit()
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse_folder)
        folder_row.addWidget(self._folder_edit, stretch=1)
        folder_row.addWidget(browse)
        layout.addLayout(folder_row)

        # ── Format options ────────────────────────────────────────────────
        fmt_group = QGroupBox("Export formats")
        fmt_layout = QVBoxLayout(fmt_group)

        self._clips_check = QCheckBox("Individual clip files (.mp4 per clip)")
        self._clips_check.setChecked(True)
        fmt_layout.addWidget(self._clips_check)

        self._merged_check = QCheckBox("Single merged file (.mp4, all clips concatenated)")
        fmt_layout.addWidget(self._merged_check)

        self._edl_check = QCheckBox("EDL reference file (.edl)")
        fmt_layout.addWidget(self._edl_check)

        self._notes_check = QCheckBox("Notes text file (.txt)")
        fmt_layout.addWidget(self._notes_check)

        self._burn_notes_check = QCheckBox("Burn notes overlay onto exported video(s)")
        self._burn_notes_check.setToolTip(
            "Renders the clip notes as yellow on-screen text in the exported .mp4 file(s).\n"
            "Requires re-encoding — slower than copy-only export."
        )
        fmt_layout.addWidget(self._burn_notes_check)

        layout.addWidget(fmt_group)

        # ── Naming preview ────────────────────────────────────────────────
        stem = Path(self._project.merged_video_path).stem
        cat_map = {c.id: c for c in self._project.categories}
        if self._clips:
            clip = self._clips[0]
            cat = cat_map.get(clip.category_id)
            cat_name = cat.name if cat else "Unknown"
            preview = f"{stem}_{cat_name}_{clip.label}_001.mp4"
        else:
            preview = f"{stem}_Category_Label_001.mp4"
        layout.addWidget(QLabel(f"Clip naming: <code>{preview}</code>"))
        layout.addWidget(QLabel(
            f"Merged file: <code>{self._pl.name}.mp4</code>"
        ))

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
        do_clips = self._clips_check.isChecked()
        do_merged = self._merged_check.isChecked()
        do_edl = self._edl_check.isChecked()
        do_notes = self._notes_check.isChecked()
        burn_notes = self._burn_notes_check.isChecked()
        if not any((do_clips, do_merged, do_edl, do_notes)):
            QMessageBox.warning(self, "Required", "Select at least one export format.")
            return

        total = (
            (len(self._clips) if do_clips else 0) +
            (1 if do_merged else 0) +
            (1 if do_edl else 0) +
            (1 if do_notes else 0)
        )
        progress = QProgressDialog("Exporting...", None, 0, total, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        step = 0
        errors = []

        try:
            if do_clips:
                from videotagger.export.ffmpeg_exporter import export_playlist_clips
                try:
                    export_playlist_clips(self._clips, self._project, folder, burn_notes)
                except RuntimeError as e:
                    errors.append(str(e))
                step += len(self._clips)
                progress.setValue(step)

            if do_merged:
                from videotagger.export.ffmpeg_exporter import export_playlist_merged
                out_path = os.path.join(folder, f"{self._pl.name}.mp4")
                try:
                    export_playlist_merged(self._clips, self._project, out_path, burn_notes)
                except RuntimeError as e:
                    errors.append(str(e))
                step += 1
                progress.setValue(step)

            if do_edl:
                from videotagger.export.edl_writer import write_edl
                edl_path = os.path.join(folder, f"{self._pl.name}.edl")
                try:
                    write_edl(self._pl.name, self._clips, self._project, edl_path)
                except Exception as e:
                    errors.append(str(e))
                step += 1
                progress.setValue(step)

            if do_notes:
                notes_path = os.path.join(folder, f"{self._pl.name}_notes.txt")
                try:
                    self._write_notes(notes_path)
                except Exception as e:
                    errors.append(str(e))
                step += 1
                progress.setValue(step)

        finally:
            progress.close()

        if errors:
            QMessageBox.critical(self, "Export errors", "\n".join(errors))
        else:
            QMessageBox.information(self, "Done", f"Exported to:\n{folder}")
            self.accept()

    def _write_notes(self, output_path: str) -> None:
        cat_map = {c.id: c for c in self._project.categories}
        lines = [f"Playlist: {self._pl.name}", "=" * 50, ""]
        for i, clip in enumerate(self._clips, 1):
            cat = cat_map.get(clip.category_id)
            cat_name = cat.name if cat else "Unknown"
            lines.append(
                f"{i:03d}. {cat_name} — {clip.label}"
                f"  [{clip.start:.1f}s – {clip.end:.1f}s]"
            )
            if clip.notes and clip.notes.strip():
                lines.append(f"     {clip.notes.strip()}")
            lines.append("")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
