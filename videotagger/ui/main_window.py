# videotagger/ui/main_window.py
from __future__ import annotations
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QStatusBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from videotagger.models.project import Project

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VideoTagger")
        self.resize(1280, 800)
        self._project: Project | None = None
        self._project_path: str | None = None
        self._signals_wired = False
        self._dirty = False
        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        self._restore_settings()

    def _setup_ui(self):
        from videotagger.ui.player_widget import PlayerWidget
        from videotagger.ui.timeline_widget import TimelineWidget
        from videotagger.ui.tag_panel import TagPanel
        from videotagger.ui.clips_panel import ClipsPanel

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self._vsplit = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(self._vsplit)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        self.player = PlayerWidget()
        self.timeline = TimelineWidget()
        self.timeline.setFixedHeight(60)
        top_layout.addWidget(self.player, stretch=1)
        top_layout.addWidget(self.timeline)
        self._vsplit.addWidget(top_widget)

        self._hsplit = QSplitter(Qt.Orientation.Horizontal)
        self.tag_panel = TagPanel()
        self.clips_panel = ClipsPanel()
        self._hsplit.addWidget(self.tag_panel)
        self._hsplit.addWidget(self.clips_panel)
        self._hsplit.setSizes([300, 700])
        self._vsplit.addWidget(self._hsplit)

        self._vsplit.setSizes([600, 200])
        self.setStatusBar(QStatusBar())

    def _setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        new_act = QAction("&New Project...", self)
        new_act.setShortcut(QKeySequence.StandardKey.New)
        new_act.triggered.connect(self._new_project)
        file_menu.addAction(new_act)

        open_act = QAction("&Open Project...", self)
        open_act.setShortcut(QKeySequence.StandardKey.Open)
        open_act.triggered.connect(self._open_project)
        file_menu.addAction(open_act)

        self._save_act = QAction("&Save", self)
        self._save_act.setShortcut(QKeySequence.StandardKey.Save)
        self._save_act.triggered.connect(self._save_project)
        self._save_act.setEnabled(False)
        file_menu.addAction(self._save_act)

        file_menu.addSeparator()
        quit_act = QAction("&Quit", self)
        quit_act.setShortcut(QKeySequence.StandardKey.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        tags_menu = menubar.addMenu("&Tags")
        manage_act = QAction("&Manage Tags...", self)
        manage_act.triggered.connect(self._open_tag_manager)
        tags_menu.addAction(manage_act)

    def _new_project(self):
        from videotagger.ui.dialogs.new_project_dialog import NewProjectDialog
        dlg = NewProjectDialog(self)
        if dlg.exec():
            self._load_project(dlg.project(), None)

    def _open_project(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Video Tagger Project (*.vtp)"
        )
        if not path:
            return
        from videotagger.data.project_manager import ProjectManager
        try:
            proj = ProjectManager.load(path)
        except (FileNotFoundError, ValueError) as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", str(e))
            return
        self._load_project(proj, path)

    def _save_project(self):
        if not self._project:
            return
        from videotagger.data.project_manager import ProjectManager
        if not self._project_path:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Project", "", "Video Tagger Project (*.vtp)"
            )
            if not path:
                return
            if not path.endswith(".vtp"):
                path += ".vtp"
            self._project_path = path
        ProjectManager.save(self._project, self._project_path)
        self._dirty = False
        self.statusBar().showMessage(f"Saved: {self._project_path}", 3000)

    def _open_tag_manager(self):
        if not self._project:
            return
        from videotagger.ui.dialogs.tag_manager_dialog import TagManagerDialog
        dlg = TagManagerDialog(self._project, self)
        dlg.exec()
        self.tag_panel.refresh(self._project)

    def _load_project(self, project: Project, path):
        import os
        if not os.path.exists(project.video_path):
            from PyQt6.QtWidgets import QMessageBox, QFileDialog
            reply = QMessageBox.warning(
                self, "Video Not Found",
                f"Video file not found:\n{project.video_path}\n\nLocate it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                new_path, _ = QFileDialog.getOpenFileName(
                    self, "Locate Video", "",
                    "Video Files (*.mp4 *.mov *.avi *.mkv *.m4v);;All Files (*)"
                )
                if not new_path:
                    return  # User cancelled
                project.video_path = new_path
            else:
                return  # User declined to locate
        from videotagger.core.tagging_engine import TaggingEngine
        self._project = project
        self._project_path = path
        self._tagging_engine = TaggingEngine()
        self._save_act.setEnabled(True)
        self.setWindowTitle(f"VideoTagger — {project.video_path}")
        self.player.load(project.video_path)
        self.timeline.set_project(project)
        self.tag_panel.refresh(project)
        self.clips_panel.refresh(project)
        self._wire_signals()

    def _wire_signals(self):
        if self._signals_wired:
            return
        self._signals_wired = True
        self.player.position_changed.connect(self.timeline.set_position)
        self.player.duration_changed.connect(self.timeline.set_duration)
        self.timeline.seek_requested.connect(self.player.seek)
        self.timeline.clip_clicked.connect(self._on_clip_clicked_in_timeline)
        self.tag_panel.label_selected.connect(self._on_label_preselected)
        self.clips_panel.clip_selected.connect(self._on_clip_selected)
        self.clips_panel.export_requested.connect(self._on_export_requested)
        self.clips_panel.present_requested.connect(self._on_present_requested)
        self.clips_panel.new_playlist_requested.connect(self._new_playlist)

    def _setup_shortcuts(self):
        from PyQt6.QtGui import QShortcut
        QShortcut("Space", self).activated.connect(self.player.toggle_play)
        QShortcut("I", self).activated.connect(self._mark_in)
        QShortcut("O", self).activated.connect(self._mark_out)
        QShortcut("Left", self).activated.connect(lambda: self.player.step(-5))
        QShortcut("Right", self).activated.connect(lambda: self.player.step(5))
        QShortcut("Shift+Left", self).activated.connect(lambda: self.player.step(-0.04))
        QShortcut("Shift+Right", self).activated.connect(lambda: self.player.step(0.04))
        QShortcut("[", self).activated.connect(
            lambda: self.player.set_rate(max(0.25, self.player.get_rate() - 0.25))
        )
        QShortcut("]", self).activated.connect(
            lambda: self.player.set_rate(min(4.0, self.player.get_rate() + 0.25))
        )
        QShortcut("Escape", self).activated.connect(self._cancel_mark)
        QShortcut("Ctrl+Z", self).activated.connect(self._undo_last_clip)
        QShortcut("F11", self).activated.connect(self._toggle_presentation)

    def _mark_in(self):
        if self._project and hasattr(self, '_tagging_engine'):
            self._tagging_engine.press_in(self.player.get_position())
            self.statusBar().showMessage(
                f"Mark IN set at {self.player.get_position():.2f}s — press O to mark end"
            )

    def _mark_out(self):
        if not self._project or not hasattr(self, '_tagging_engine'):
            return
        from videotagger.core.tagging_engine import TaggingState
        if self._tagging_engine.state != TaggingState.MARKING:
            return
        try:
            start, end = self._tagging_engine.press_out(self.player.get_position())
        except ValueError as e:
            self.statusBar().showMessage(str(e), 3000)
            return
        preset_cat = getattr(self, '_preset_category_id', None)
        preset_lbl = getattr(self, '_preset_label', None)
        from videotagger.ui.dialogs.new_clip_dialog import NewClipDialog
        dlg = NewClipDialog(self._project, start, end, preset_cat, preset_lbl, self)
        if dlg.exec():
            clip = dlg.clip()
            self._project.clips.append(clip)
            self._dirty = True
            self.timeline.set_project(self._project)
            self.clips_panel.refresh(self._project)
            self.statusBar().showMessage(
                f"Clip added: {clip.label} ({start:.1f}s – {end:.1f}s)", 3000
            )

    def _cancel_mark(self):
        if hasattr(self, '_tagging_engine'):
            self._tagging_engine.cancel()
            self.statusBar().showMessage("Clip mark cancelled", 2000)

    def _undo_last_clip(self):
        if self._project and self._project.clips:
            removed = self._project.clips.pop()
            self._dirty = True
            self.timeline.set_project(self._project)
            self.clips_panel.refresh(self._project)
            self.statusBar().showMessage(f"Undo: removed clip '{removed.label}'", 3000)

    def _on_label_preselected(self, category_id: str, label: str):
        self._preset_category_id = category_id
        self._preset_label = label
        self.statusBar().showMessage(f"Pre-selected: {label} — press I to start marking", 3000)

    def _on_clip_clicked_in_timeline(self, clip_id: str):
        if self._project:
            clip = next((c for c in self._project.clips if c.id == clip_id), None)
            if clip:
                self.player.seek(clip.start)

    def _on_clip_selected(self, clip_id: str):
        if self._project:
            clip = next((c for c in self._project.clips if c.id == clip_id), None)
            if clip:
                self.player.seek(clip.start)

    def _new_playlist(self):
        from PyQt6.QtWidgets import QInputDialog
        from videotagger.core.playlist_builder import PlaylistBuilder
        name, ok = QInputDialog.getText(self, "New Playlist", "Playlist name:")
        if ok and name.strip():
            PlaylistBuilder(self._project).create_playlist(name.strip())
            self.clips_panel.refresh(self._project)

    def _on_export_requested(self, playlist_id: str):
        from videotagger.ui.dialogs.export_dialog import ExportDialog
        dlg = ExportDialog(self._project, playlist_id, self)
        dlg.exec()

    def _on_present_requested(self, playlist_id: str):
        from videotagger.ui.presentation_window import PresentationWindow
        from videotagger.core.playlist_builder import PlaylistBuilder
        clips = PlaylistBuilder(self._project).get_clips(playlist_id)
        pl = next(p for p in self._project.playlists if p.id == playlist_id)
        category_map = {cat.id: cat.name for cat in self._project.categories}
        self._presentation = PresentationWindow(
            self._project.video_path, clips, pl.name, category_map, self
        )
        self._presentation.showFullScreen()

    def _toggle_presentation(self):
        pass  # F11 from main window — no-op unless a playlist is active

    def closeEvent(self, event):
        self._save_settings()
        if self._project and self._dirty:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save_project()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        event.accept()

    def _restore_settings(self):
        from videotagger.data.settings_manager import SettingsManager
        import base64
        s = SettingsManager.load()
        if "geometry" in s:
            from PyQt6.QtCore import QByteArray
            self.restoreGeometry(QByteArray(base64.b64decode(s["geometry"])))
        self._recent_files = s.get("recent_files", [])

    def _save_settings(self):
        from videotagger.data.settings_manager import SettingsManager
        import base64
        SettingsManager.save({
            "geometry": base64.b64encode(bytes(self.saveGeometry())).decode(),
            "recent_files": getattr(self, "_recent_files", []),
        })
