# videotagger/ui/main_window.py
from __future__ import annotations
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QStatusBar, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QPixmap, QIcon
from videotagger.models.project import Project
from videotagger.core.project_document import ProjectDocument
from videotagger.ui import theme

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VideoTagger")
        self.resize(1280, 800)
        self._doc: ProjectDocument | None = None
        self._signals_wired = False
        # Resolve the accent BEFORE building the UI so inline-styled widgets
        # (header, transport, keycaps) build in the same accent the stylesheet uses.
        from videotagger.data.settings_manager import SettingsManager
        self._settings = SettingsManager.load()
        self._accent_color = self._settings.get("accent_color", theme.DEFAULT_ACCENT)
        theme.set_accent(self._accent_color)
        self._apply_style()
        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        self._restore_settings()

    def _apply_style(self):
        from videotagger.ui.style import build_stylesheet
        self.setStyleSheet(build_stylesheet(theme.ACCENT))
        self._apply_window_icon()

    @staticmethod
    def _tint_pixmap(src: QPixmap, color: str) -> QPixmap:
        """Tint a grayscale+alpha pixmap by accent (accent × luminance), preserving alpha."""
        from PyQt6.QtGui import QPainter, QColor
        out = QPixmap(src.size())
        out.fill(Qt.GlobalColor.transparent)
        p = QPainter(out)
        p.drawPixmap(0, 0, src)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
        p.fillRect(out.rect(), QColor(color))
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        p.drawPixmap(0, 0, src)  # restore the master's alpha
        p.end()
        return out

    def _apply_logo_tint(self):
        if getattr(self, "_logo_master", None) is None or self._logo_master.isNull():
            return
        src = self._logo_master.scaledToHeight(42, Qt.TransformationMode.SmoothTransformation)
        self._logo_lbl.setPixmap(self._tint_pixmap(src, theme.ACCENT))

    def _refresh_wordmark(self):
        self._title_label.setText(
            f'<span style="color:{theme.TEXT};">VIDEO</span>'
            f'<span style="color:{theme.ACCENT};">TAGGER</span>'
        )

    def _apply_window_icon(self):
        logo_path = self._resource_path("logo_mark.png")
        if not logo_path:
            return
        master = QPixmap(logo_path)
        if master.isNull():
            return
        src = master.scaledToHeight(256, Qt.TransformationMode.SmoothTransformation)
        self.setWindowIcon(QIcon(self._tint_pixmap(src, theme.ACCENT)))

    @staticmethod
    def _resource_path(filename: str) -> str | None:
        """Return absolute path to a bundled resource, works frozen and unfrozen."""
        import sys, os
        if getattr(sys, "frozen", False):
            base = sys._MEIPASS
        else:
            base = os.path.join(os.path.dirname(__file__), "..", "resources")
        path = os.path.normpath(os.path.join(base, "videotagger", "resources", filename)) \
            if getattr(sys, "frozen", False) else \
            os.path.normpath(os.path.join(base, filename))
        return path if os.path.exists(path) else None

    def _setup_ui(self):
        from videotagger.ui.player_widget import PlayerWidget
        from videotagger.ui.timeline_widget import TimelineWidget
        from videotagger.ui.tag_panel import TagPanel
        from videotagger.ui.clips_panel import ClipsPanel

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {theme.INK}, stop:1 {theme.INK_DEEP});"
            f"border-bottom: 1px solid {theme.LINE};"
        )
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(14, 0, 16, 0)
        header_row.setSpacing(10)

        self._logo_lbl = QLabel()
        self._logo_lbl.setStyleSheet("background: transparent;")
        logo_path = self._resource_path("logo_mark.png")
        self._logo_master = QPixmap(logo_path) if logo_path else QPixmap()
        self._apply_logo_tint()
        header_row.addWidget(self._logo_lbl)

        self._title_label = QLabel()
        self._title_label.setStyleSheet(
            f"background: transparent;"
            f"font-family: {theme.FONT_DISPLAY}; font-size: 14pt;"
            f"font-weight: 700; letter-spacing: 1.5px;"
        )
        self._refresh_wordmark()
        header_row.addWidget(self._title_label)

        self._version_badge = QLabel("v2.1")
        self._version_badge.setStyleSheet(self._badge_style())
        header_row.addWidget(self._version_badge)
        header_row.addStretch()

        self._file_label = QLabel("")
        self._file_label.setStyleSheet(
            f"background: transparent; color: {theme.FAINT};"
            f"font-size: 8pt; font-family: {theme.FONT_MONO};"
        )
        header_row.addWidget(self._file_label)
        layout.addWidget(header)

        # ── Main content ───────────────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(4)
        layout.addWidget(content, stretch=1)

        self._vsplit = QSplitter(Qt.Orientation.Vertical)
        content_layout.addWidget(self._vsplit)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        from videotagger.ui.shortcut_bar import ShortcutBar
        self.player = PlayerWidget()
        self.timeline = TimelineWidget()
        self.timeline.setFixedHeight(60)
        self.shortcut_bar = ShortcutBar()
        top_layout.addWidget(self.player, stretch=1)
        top_layout.addWidget(self.shortcut_bar)
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

        self._import_act = QAction("&Import Timestamps...", self)
        self._import_act.triggered.connect(self._import_timestamps)
        self._import_act.setEnabled(False)
        file_menu.addAction(self._import_act)

        self._package_act = QAction("&Package Project…", self)
        self._package_act.triggered.connect(self._package_project)
        self._package_act.setEnabled(False)
        file_menu.addAction(self._package_act)

        file_menu.addSeparator()
        quit_act = QAction("&Quit", self)
        quit_act.setShortcut(QKeySequence.StandardKey.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        video_menu = menubar.addMenu("&Video")
        self._periods_act = QAction("Manage &Periods…", self)
        self._periods_act.triggered.connect(self._manage_periods)
        self._periods_act.setEnabled(False)
        video_menu.addAction(self._periods_act)
        self._angles_act = QAction("Manage &Angles…", self)
        self._angles_act.triggered.connect(self._manage_angles)
        self._angles_act.setEnabled(False)
        video_menu.addAction(self._angles_act)

        tags_menu = menubar.addMenu("&Tags")
        manage_act = QAction("&Manage Tags...", self)
        manage_act.triggered.connect(self._open_tag_manager)
        tags_menu.addAction(manage_act)

        settings_menu = menubar.addMenu("&Settings")
        color_act = QAction("Team &Color...", self)
        color_act.triggered.connect(self._choose_team_color)
        settings_menu.addAction(color_act)

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
        if not self._doc:
            return
        if self._doc.path is None:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Project", "", "Video Tagger Project (*.vtp)"
            )
            if not path:
                return
            if not path.endswith(".vtp"):
                path += ".vtp"
            self._doc.save_as(path)
        else:
            self._doc.save()
        self.statusBar().showMessage(f"Saved: {self._doc.path}", 3000)

    def _open_tag_manager(self):
        if not self._doc:
            return
        from videotagger.ui.dialogs.tag_manager_dialog import TagManagerDialog
        dlg = TagManagerDialog(self._doc, self)
        dlg.exec()

    def _load_project(self, project: Project, path):
        import os
        if not os.path.exists(project.merged_video_path):
            from PyQt6.QtWidgets import QMessageBox, QFileDialog
            msg = (
                f"Merged video not found:\n{project.merged_video_path}\n\n"
                "Would you like to locate the merged file, or re-merge from sources?"
            )
            reply = QMessageBox.warning(
                self, "Video Not Found", msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Yes:
                new_path, _ = QFileDialog.getOpenFileName(
                    self, "Locate Merged Video", "",
                    "Video Files (*.mp4 *.mov *.avi *.mkv *.m4v);;All Files (*)",
                )
                if not new_path:
                    return
                project.merged_video_path = new_path
            elif reply == QMessageBox.StandardButton.No:
                from videotagger.core.video_merger import VideoMerger
                from videotagger.ui.dialogs.merge_progress_dialog import MergeProgressDialog
                from videotagger.export.ffmpeg_exporter import _ffmpeg_path
                merger = VideoMerger(_ffmpeg_path())
                dlg = MergeProgressDialog(
                    merger, project.source_video_paths,
                    project.merged_video_path, self,
                )
                if not dlg.exec() or not dlg.was_successful():
                    return
            else:
                return

        from videotagger.core.tagging_engine import TaggingEngine
        self._doc = ProjectDocument(project, path)
        self._doc.subscribe(self._refresh_all)
        self._tagging_engine = TaggingEngine()
        self._save_act.setEnabled(True)
        self._import_act.setEnabled(True)
        self._package_act.setEnabled(True)
        self._periods_act.setEnabled(True)
        self._angles_act.setEnabled(True)
        self.setWindowTitle("VideoTagger")
        self._file_label.setText(os.path.basename(project.merged_video_path))
        self.player.load(project.merged_video_path)
        self._refresh_all()
        self._wire_signals()
        self._apply_secondary_angle()

    def _refresh_all(self):
        """Single subscriber to the document's `changed`: repaint every panel."""
        if not self._doc:
            return
        project = self._doc.project
        self.timeline.set_project(project)
        self.clips_panel.refresh(project)
        self.tag_panel.refresh(project)

    def _apply_secondary_angle(self):
        """Wire the project's secondary angle (if any) into the dual-decode player."""
        if self._doc and self._doc.project.angles:
            from videotagger.core.angle_sync import angle_covers, map_to_angle
            angle = self._doc.project.angles[0]
            periods = self._doc.project.periods
            self.player.set_secondary_angle(
                angle.merged_video_path,
                lambda t: map_to_angle(periods, angle, t),
                primary_name="Primary",
                secondary_name=angle.name,
                covers=lambda t: angle_covers(periods, angle, t),
            )
            self.shortcut_bar.set_angle_available(True)
        else:
            self.player.clear_secondary_angle()
            self.shortcut_bar.set_angle_available(False)

    def _manage_periods(self):
        if not self._doc:
            return
        from videotagger.ui.dialogs.periods_dialog import ManagePeriodsDialog
        dlg = ManagePeriodsDialog(self._doc, self)
        if dlg.exec():
            self._save_act.setEnabled(True)
            self.statusBar().showMessage("Periods updated", 3000)

    def _manage_angles(self):
        if not self._doc:
            return
        from videotagger.ui.dialogs.angle_sync_dialog import AngleSyncDialog
        dlg = AngleSyncDialog(self._doc, self)
        if dlg.exec():
            if getattr(dlg, "_primary_swapped", False):
                import os
                self.player.clear_secondary_angle()
                self.player.load(self._doc.project.merged_video_path)
                self._file_label.setText(os.path.basename(self._doc.project.merged_video_path))
                self.statusBar().showMessage("Primary angle changed", 3000)
            else:
                self.statusBar().showMessage("Angle sync updated", 3000)
            self._apply_secondary_angle()
            self._save_act.setEnabled(True)

    def _package_project(self):
        if not self._doc:
            return
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import copy, os, shutil
        from videotagger.data.project_manager import ProjectManager

        folder = QFileDialog.getExistingDirectory(self, "Choose Package Destination")
        if not folder:
            return

        if self._doc.path:
            proj_stem = os.path.splitext(os.path.basename(self._doc.path))[0]
        else:
            proj_stem = "VideoTaggerProject"

        pkg_dir = os.path.join(folder, proj_stem)
        try:
            os.makedirs(pkg_dir, exist_ok=True)
            shutil.copy2(self._doc.project.merged_video_path, os.path.join(pkg_dir, "video.mp4"))
            pkg_project = copy.copy(self._doc.project)
            pkg_project.merged_video_path = "./video.mp4"
            pkg_project.source_video_paths = ["./video.mp4"]
            ProjectManager.save(pkg_project, os.path.join(pkg_dir, "project.vtp"))
        except Exception as exc:
            QMessageBox.critical(self, "Package Failed", str(exc))
            return

        QMessageBox.information(
            self, "Packaged",
            f"Project packaged successfully:\n{pkg_dir}",
        )

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
        self.clips_panel.add_clips_to_playlist_requested.connect(self._on_add_clips_to_playlist)
        self.clips_panel.delete_playlist_requested.connect(self._on_delete_playlist)
        self.clips_panel.filter_changed.connect(self.timeline.set_filter)

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
        QShortcut("+", self).activated.connect(self.player.zoom_in)
        QShortcut("=", self).activated.connect(self.player.zoom_in)
        QShortcut("-", self).activated.connect(self.player.zoom_out)
        QShortcut("0", self).activated.connect(self.player.reset_zoom)
        QShortcut("V", self).activated.connect(self.player.switch_angle)
        QShortcut("Escape", self).activated.connect(self._cancel_mark)
        QShortcut("Ctrl+Z", self).activated.connect(self._undo_last_clip)
        QShortcut("F11", self).activated.connect(self._toggle_presentation)

    def _mark_in(self):
        if self._doc and hasattr(self, '_tagging_engine'):
            pos = self.player.get_position()
            self._tagging_engine.press_in(pos)
            self.shortcut_bar.set_marking(pos)
            self.statusBar().showMessage(
                f"Mark IN set at {pos:.2f}s — press O to mark end"
            )

    def _mark_out(self):
        if not self._doc or not hasattr(self, '_tagging_engine'):
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
        dlg = NewClipDialog(self._doc.project, start, end, preset_cat, preset_lbl, self)
        if dlg.exec():
            clip = dlg.clip()
            self._doc.add_clip(clip)
            self.statusBar().showMessage(
                f"Clip added: {clip.label} ({start:.1f}s – {end:.1f}s)", 3000
            )
        self.shortcut_bar.set_idle()

    def _cancel_mark(self):
        if hasattr(self, '_tagging_engine'):
            self._tagging_engine.cancel()
            self.shortcut_bar.set_idle()
            self.statusBar().showMessage("Clip mark cancelled", 2000)

    def _undo_last_clip(self):
        if not self._doc:
            return
        removed = self._doc.remove_last_clip()
        if removed:
            self.statusBar().showMessage(f"Undo: removed clip '{removed.label}'", 3000)

    def _on_label_preselected(self, category_id: str, label: str):
        self._preset_category_id = category_id
        self._preset_label = label
        self.statusBar().showMessage(f"Pre-selected: {label} — press I to start marking", 3000)

    def _on_clip_clicked_in_timeline(self, clip_id: str):
        if self._doc:
            clip = next((c for c in self._doc.project.clips if c.id == clip_id), None)
            if clip:
                self.player.seek(clip.start)

    def _on_clip_selected(self, clip_id: str):
        if self._doc:
            clip = next((c for c in self._doc.project.clips if c.id == clip_id), None)
            if clip:
                self.player.seek(clip.start)

    def _new_playlist(self):
        from PyQt6.QtWidgets import QInputDialog
        if not self._doc:
            return
        name, ok = QInputDialog.getText(self, "New Playlist", "Playlist name:")
        if ok and name.strip():
            self._doc.new_playlist(name.strip())

    def _on_add_clips_to_playlist(self, playlist_id: str, clip_ids: list):
        if not self._doc:
            return
        for clip_id in clip_ids:
            self._doc.add_clip_to_playlist(playlist_id, clip_id)

    def _on_delete_playlist(self, playlist_id: str):
        if self._doc:
            self._doc.delete_playlist(playlist_id)

    def _on_export_requested(self, playlist_id: str):
        from videotagger.ui.dialogs.export_dialog import ExportDialog
        dlg = ExportDialog(self._doc.project, playlist_id, self)
        dlg.exec()

    def _on_present_requested(self, playlist_id: str):
        from videotagger.ui.presentation_window import PresentationWindow
        if not self._doc:
            return
        pl = next((p for p in self._doc.project.playlists if p.id == playlist_id), None)
        if pl is None:
            return
        clips = self._doc.clips_of(playlist_id)
        category_map = {cat.id: cat.name for cat in self._doc.project.categories}
        # Cleanly destroy any previous presentation window before creating a new
        # one — the old QMediaPlayer must be stopped before its parent widget is
        # garbage-collected, otherwise Qt's C++ layer crashes.
        if hasattr(self, '_presentation') and self._presentation is not None:
            self._presentation.close()
            self._presentation.deleteLater()
            self._presentation = None
        self._presentation = PresentationWindow(
            self._doc.project.merged_video_path, clips, pl.name, category_map, self
        )
        self._presentation.closed.connect(self._on_presentation_closed)
        self._presentation.showFullScreen()

    def _on_presentation_closed(self):
        if self._presentation is not None:
            self._presentation.deleteLater()
            self._presentation = None

    def _import_timestamps(self):
        if not self._doc:
            return
        from videotagger.ui.dialogs.import_timestamps_dialog import ImportTimestampsDialog
        dlg = ImportTimestampsDialog(self._doc.project, self)
        if dlg.exec():
            clips = dlg.clips()
            self._doc.add_clips(clips)
            self.statusBar().showMessage(f"Imported {len(clips)} clip(s) from timestamps", 3000)

    def _toggle_presentation(self):
        pass  # F11 from main window — no-op unless a playlist is active

    def closeEvent(self, event):
        self._save_settings()
        if self._doc and self._doc.is_dirty:
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

    def _choose_team_color(self):
        from PyQt6.QtWidgets import QColorDialog
        from PyQt6.QtGui import QColor
        current = getattr(self, "_accent_color", theme.ACCENT)
        color = QColorDialog.getColor(QColor(current), self, "Choose Team Accent Color")
        if color.isValid():
            self._accent_color = color.name()
            self._apply_accent(self._accent_color)

    def _badge_style(self) -> str:
        return (
            f"background: {theme.shade(theme.ACCENT, 0.16)}; color: {theme.ACCENT};"
            f"font-family: {theme.FONT_MONO}; font-size: 7.5pt;"
            f"font-weight: 600; letter-spacing: 1px;"
            f"border: 1px solid {theme.ACCENT_DIM}; border-radius: 4px;"
            f"padding: 2px 6px;"
        )

    def _apply_accent(self, accent: str):
        """Apply an accent across the whole UI — stylesheet and inline-styled widgets."""
        theme.set_accent(accent)
        from videotagger.ui.style import build_stylesheet
        self.setStyleSheet(build_stylesheet(accent))
        # Restyle the inline-accent widgets the stylesheet doesn't reach.
        self._version_badge.setStyleSheet(self._badge_style())
        self._apply_logo_tint()
        self._refresh_wordmark()
        self._apply_window_icon()
        self.player.apply_accent()
        self.shortcut_bar.set_idle()
        self.timeline.update()

    def _restore_settings(self):
        import base64
        s = self._settings
        if "geometry" in s:
            from PyQt6.QtCore import QByteArray
            self.restoreGeometry(QByteArray(base64.b64decode(s["geometry"])))
        self._recent_files = s.get("recent_files", [])
        # Accent was already resolved and applied in __init__.

    def _save_settings(self):
        from videotagger.data.settings_manager import SettingsManager
        import base64
        SettingsManager.save({
            "geometry": base64.b64encode(bytes(self.saveGeometry())).decode(),
            "recent_files": getattr(self, "_recent_files", []),
            "accent_color": getattr(self, "_accent_color", theme.ACCENT),
        })
