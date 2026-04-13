# videotagger/ui/clips_panel.py
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QListWidget, QListWidgetItem, QHeaderView, QAbstractItemView, QMenu, QLineEdit, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt
from videotagger.models.project import Project

class ClipsPanel(QWidget):
    clip_selected = pyqtSignal(str)
    playlist_selected = pyqtSignal(str)
    export_requested = pyqtSignal(str)
    present_requested = pyqtSignal(str)
    new_playlist_requested = pyqtSignal()
    filter_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project: Project | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        # Search bar
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.addWidget(QLabel("Search:"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter by label, category, or notes…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_filter_changed)
        search_row.addWidget(self._search)
        layout.addLayout(search_row)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)
        self._clips_table = self._make_clips_table()
        self._playlists_list = self._make_playlists_list()
        self._tabs.addTab(self._clips_table, "Clips")
        self._tabs.addTab(self._playlists_list, "Playlists")
        from videotagger.ui.help_panel import HelpPanel
        self._tabs.addTab(HelpPanel(), "Help")

    def _make_clips_table(self) -> QTableWidget:
        t = QTableWidget(0, 5)
        t.setHorizontalHeaderLabels(["Category", "Label", "Start", "End", "Notes"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        t.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
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

    def _on_filter_changed(self, text: str):
        self._apply_table_filter(text)
        self.filter_changed.emit(text)

    def _apply_table_filter(self, text: str):
        q = text.lower().strip()
        if not self._project:
            return
        cat_map = {c.id: c for c in self._project.categories}
        for row in range(self._clips_table.rowCount()):
            clip_id = self._clips_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            clip = next((c for c in self._project.clips if c.id == clip_id), None)
            if not clip or not q:
                self._clips_table.setRowHidden(row, False)
                continue
            cat = cat_map.get(clip.category_id)
            haystack = " ".join([clip.label, clip.notes or "", cat.name if cat else ""]).lower()
            self._clips_table.setRowHidden(row, q not in haystack)

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
            self._clips_table.setItem(row, 4, QTableWidgetItem(clip.notes or ""))
        # Re-apply current filter after repopulating
        self._apply_table_filter(self._search.text())

    def _refresh_playlists(self):
        if not self._project:
            return
        self._playlists_list.clear()
        for pl in self._project.playlists:
            item = QListWidgetItem(f"{pl.name} ({len(pl.clip_ids)} clips)")
            item.setData(Qt.ItemDataRole.UserRole, pl.id)
            self._playlists_list.addItem(item)

    def _on_clip_clicked(self, row, col):
        # Only seek when a single row is selected (not during multi-select)
        if len(self._clips_table.selectedItems()) // self._clips_table.columnCount() == 1:
            item = self._clips_table.item(row, 0)
            if item:
                self.clip_selected.emit(item.data(Qt.ItemDataRole.UserRole))

    def _on_playlist_clicked(self, item: QListWidgetItem):
        self.playlist_selected.emit(item.data(Qt.ItemDataRole.UserRole))

    def _selected_clip_ids(self) -> list[str]:
        """Return clip IDs for all currently selected (visible) rows."""
        seen = set()
        ids = []
        for idx in self._clips_table.selectedIndexes():
            row = idx.row()
            if row in seen:
                continue
            seen.add(row)
            item = self._clips_table.item(row, 0)
            if item:
                ids.append(item.data(Qt.ItemDataRole.UserRole))
        return ids

    def _clips_context_menu(self, pos):
        if not self._project:
            return
        item = self._clips_table.itemAt(pos)
        if not item:
            return
        clip_ids = self._selected_clip_ids()
        if not clip_ids:
            clip_ids = [self._clips_table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)]
        n = len(clip_ids)
        label = f"{n} clip{'s' if n > 1 else ''}"
        menu = QMenu(self)
        for pl in self._project.playlists:
            act = menu.addAction(f"Add {label} to: {pl.name}")
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
                builder = PlaylistBuilder(self._project)
                for clip_id in clip_ids:
                    builder.add_clip(chosen.data(), clip_id)
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
