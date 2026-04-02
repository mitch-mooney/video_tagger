from typing import List
from videotagger.models.project import Clip, Playlist, Project

class PlaylistBuilder:
    def __init__(self, project: Project):
        self._project = project

    def create_playlist(self, name: str) -> Playlist:
        pl = Playlist(name=name)
        self._project.playlists.append(pl)
        return pl

    def delete_playlist(self, playlist_id: str) -> None:
        self._project.playlists = [p for p in self._project.playlists if p.id != playlist_id]

    def add_clip(self, playlist_id: str, clip_id: str) -> None:
        pl = self._get(playlist_id)
        if clip_id not in pl.clip_ids:
            pl.clip_ids.append(clip_id)

    def remove_clip(self, playlist_id: str, clip_id: str) -> None:
        pl = self._get(playlist_id)
        pl.clip_ids = [c for c in pl.clip_ids if c != clip_id]

    def reorder_clips(self, playlist_id: str, clip_ids: List[str]) -> None:
        pl = self._get(playlist_id)
        pl.clip_ids = clip_ids

    def get_clips(self, playlist_id: str) -> List[Clip]:
        pl = self._get(playlist_id)
        clip_map = {c.id: c for c in self._project.clips}
        return [clip_map[cid] for cid in pl.clip_ids if cid in clip_map]

    def _get(self, playlist_id: str) -> Playlist:
        for p in self._project.playlists:
            if p.id == playlist_id:
                return p
        raise KeyError(f"Playlist not found: {playlist_id}")
