"""The live editing object for a project — the single write path for every mutation.

``ProjectDocument`` owns the in-memory :class:`Project`, its file path, and the dirty flag.
Every mutation (clips, playlists, categories, secondary angle) goes through a method here,
which sets dirty and fires one coarse ``changed`` notification. Reads go through ``.project``.

Pure Python — no Qt — so edits are testable headless (see test_project_document.py). The UI
(``MainWindow``) is the sole subscriber and bridges ``changed`` to a refresh of the panels.
Persistence bytes are delegated to :class:`ProjectManager` (see ADR 0001).
"""
from __future__ import annotations

from typing import Callable, List, Optional

from videotagger.data.project_manager import ProjectManager
from videotagger.models.project import (
    Category, Clip, Period, Playlist, Project, VideoAngle,
)


class ProjectDocument:
    def __init__(self, project: Project, path: Optional[str] = None):
        self._project = project
        self._path = path
        self._dirty = False
        self._listeners: List[Callable[[], None]] = []

    # ── access ───────────────────────────────────────────────────────────

    @property
    def project(self) -> Project:
        return self._project

    @property
    def path(self) -> Optional[str]:
        return self._path

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    # ── notification ─────────────────────────────────────────────────────

    def subscribe(self, callback: Callable[[], None]) -> None:
        """Register a listener called (with no args) after every change."""
        self._listeners.append(callback)

    def _changed(self) -> None:
        self._dirty = True
        for callback in self._listeners:
            callback()

    # ── clips ────────────────────────────────────────────────────────────

    def add_clip(self, clip: Clip) -> None:
        self._project.clips.append(clip)
        self._changed()

    def add_clips(self, clips: List[Clip]) -> None:
        if not clips:
            return
        self._project.clips.extend(clips)
        self._changed()

    def remove_last_clip(self) -> Optional[Clip]:
        if not self._project.clips:
            return None
        clip = self._project.clips.pop()
        self._changed()
        return clip

    # ── secondary angle ──────────────────────────────────────────────────

    def set_secondary_angle(self, periods: List[Period], angle: VideoAngle) -> None:
        self._project.periods = list(periods)
        self._project.angles = [angle]
        self._changed()

    def clear_secondary_angle(self) -> None:
        self._project.angles = []
        self._changed()

    # ── categories ───────────────────────────────────────────────────────

    def set_categories(self, categories: List[Category]) -> None:
        self._project.categories = list(categories)
        self._changed()

    # ── playlists ────────────────────────────────────────────────────────

    def new_playlist(self, name: str) -> Playlist:
        playlist = Playlist(name=name)
        self._project.playlists.append(playlist)
        self._changed()
        return playlist

    def delete_playlist(self, playlist_id: str) -> None:
        self._project.playlists = [
            p for p in self._project.playlists if p.id != playlist_id
        ]
        self._changed()

    def add_clip_to_playlist(self, playlist_id: str, clip_id: str) -> None:
        playlist = self._playlist(playlist_id)
        if clip_id not in playlist.clip_ids:
            playlist.clip_ids.append(clip_id)
            self._changed()

    def remove_clip_from_playlist(self, playlist_id: str, clip_id: str) -> None:
        playlist = self._playlist(playlist_id)
        playlist.clip_ids = [c for c in playlist.clip_ids if c != clip_id]
        self._changed()

    def reorder_playlist(self, playlist_id: str, clip_ids: List[str]) -> None:
        playlist = self._playlist(playlist_id)
        playlist.clip_ids = list(clip_ids)
        self._changed()

    def clips_of(self, playlist_id: str) -> List[Clip]:
        playlist = self._playlist(playlist_id)
        clip_map = {c.id: c for c in self._project.clips}
        return [clip_map[cid] for cid in playlist.clip_ids if cid in clip_map]

    def _playlist(self, playlist_id: str) -> Playlist:
        for p in self._project.playlists:
            if p.id == playlist_id:
                return p
        raise KeyError(f"Playlist not found: {playlist_id}")

    # ── persistence ──────────────────────────────────────────────────────

    def save(self) -> None:
        if self._path is None:
            raise ValueError("No path set; use save_as(path)")
        ProjectManager.save(self._project, self._path)
        self._dirty = False

    def save_as(self, path: str) -> None:
        self._path = path
        self.save()
