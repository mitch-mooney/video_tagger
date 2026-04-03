# videotagger/ui/clips_panel.py
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QListWidget, QListWidgetItem, QHeaderView, QAbstractItemView, QMenu
)
from PyQt6.QtCore import pyqtSignal, Qt
from videotagger.models.project import Project

class ClipsPanel(QWidget):
    clip_selected = pyqtSignal(str)
    playlist_selected = pyqtSignal(str)
    export_requested = pyqtSignal(str)
    present_requested = pyqtSignal(str)
    new_playlist_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project: Project | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)
        self._clips_table = self._make_clips_table()
        self._playlists_list = self._make_playlists_list()
        self._tabs.addTab(self._clips_table, "Clips")
        self._tabs.addTab(self._playlists_list, "Playlists")

    def _make_clips_table(self) -> QTableWidget:
        t = QTableWidget(0, 4)
        t.setHorizontalHeaderLabels(["Category", "Label", "Start", "End"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.cellClicked.connect(self._on_clip_clicked)
        t.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        t.customContextMenuRequested.connect(self._clips_context_menu)
        return t

    def _make_playlists_list(self) -> QListWidget:
        lst = QListWidget()
        lst.itemClicked.connect(self._on_playlist_clicked)
        lst.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        lst.customContextMenuRequested.connect(self._playlists_context_menu)
        return lst

    def refresh(self, project: Project) -> None:
        self._project = project
        self._refresh_clips()
        self._refresh_playlists()

    def _refresh_clips(self):
        if not self._project:
            return
        cat_map = {c.id: c for c in self._project.categories}
        self._clips_table.setRowCount(0)
        for clip in self._project.clips:
            row = self._clips_table.rowCount()
            self._clips_table.insertRow(row)
            cat = cat_map.get(clip.category_id)
            item0 = QTableWidgetItem(cat.name if cat else "")
            item0.setData(Qt.ItemDataRole.UserRole, clip.id)
            self._clips_table.setItem(row, 0, item0)
            self._clips_table.setItem(row, 1, QTableWidgetItem(clip.label))
            self._clips_table.setItem(row, 2, QTableWidgetItem(self._fmt(clip.start)))
            self._clips_table.setItem(row, 3, QTableWidgetItem(self._fmt(clip.end)))

    def _refresh_playlists(self):
        if not self._project:
            return
        self._playlists_list.clear()
        for pl in self._project.playlists:
            item = QListWidgetItem(f"{pl.name} ({len(pl.clip_ids)} clips)")
            item.setData(Qt.ItemDataRole.UserRole, pl.id)
            self._playlists_list.addItem(item)

    def _on_clip_clicked(self, row, col):
        item = self._clips_table.item(row, 0)
        if item:
            self.clip_selected.emit(item.data(Qt.ItemDataRole.UserRole))

    def _on_playlist_clicked(self, item: QListWidgetItem):
        self.playlist_selected.emit(item.data(Qt.ItemDataRole.UserRole))

    def _clips_context_menu(self, pos):
        if not self._project:
            return
        item = self._clips_table.itemAt(pos)
        if not item:
            return
        clip_id = self._clips_table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        for pl in self._project.playlists:
            act = menu.addAction(f"Add to: {pl.name}")
            act.setData(pl.id)
        if self._project.playlists:
            menu.addSeparator()
        new_act = menu.addAction("New playlist...")
        new_act.setData("__new__")
        chosen = menu.exec(self._clips_table.mapToGlobal(pos))
        if chosen:
            if chosen.data() == "__new__":
                self.new_playlist_requested.emit()
            else:
                from videotagger.core.playlist_builder import PlaylistBuilder
                PlaylistBuilder(self._project).add_clip(chosen.data(), clip_id)
                self._refresh_playlists()

    def _playlists_context_menu(self, pos):
        item = self._playlists_list.itemAt(pos)
        if not item:
            return
        pl_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        present_act = menu.addAction("Present Playlist")
        export_act = menu.addAction("Export Playlist...")
        menu.addSeparator()
        delete_act = menu.addAction("Delete Playlist")
        chosen = menu.exec(self._playlists_list.mapToGlobal(pos))
        if chosen == present_act:
            self.present_requested.emit(pl_id)
        elif chosen == export_act:
            self.export_requested.emit(pl_id)
        elif chosen == delete_act:
            from videotagger.core.playlist_builder import PlaylistBuilder
            PlaylistBuilder(self._project).delete_playlist(pl_id)
            self._refresh_playlists()

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        ms = int((seconds - s) * 10)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}.{ms}"
