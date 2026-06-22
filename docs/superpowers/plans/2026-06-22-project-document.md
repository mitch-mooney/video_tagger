# Plan — Deepen the project document

Candidate #1 from the 2026-06-22 architecture review. Introduce `ProjectDocument`: a
single, Qt-free write path for every project mutation, owning the in-memory project, its
path, and the dirty flag. Built test-first.

## Decisions (from grilling)

- Plain Python, **not** a `QObject`. Listener via `subscribe(callback)`. `MainWindow` is the
  sole subscriber and bridges `changed` → refresh-all.
- Owns edits + dirty + path + `save`/`save_as`; delegates bytes to `ProjectManager`.
- Lives at `core/project_document.py`, class `ProjectDocument`. New `core → data` edge is
  recorded in ADR 0001.
- **Semantic** mutation methods (not a generic edit wrapper). Reads via `doc.project`.
- **Full scope**: every mutation routes through the document — including `ClipsPanel`'s
  context-menu playlist edits and `TagManagerDialog`'s category edits (both currently bypass
  dirty tracking — a real bug).
- **Coarse** notification: one `changed` callback → `MainWindow._refresh_all()`.
- Widgets: `ClipsPanel` **emits requests**; modal dialogs **hold the document** and commit.
- Categories: **coarse** `set_categories(cats)` — `TagManagerDialog` edits a deep copy and
  commits on Done.
- Undo stays minimal: `remove_last_clip()`. No undo stack.
- Construction: `ProjectDocument(project, path=None)`. Video-not-found UI stays in
  `MainWindow`. `is_dirty` starts `False` (new unsaved project doesn't prompt — preserved).
- `PlaylistBuilder` is fully absorbed and deleted (this completes candidate #5).

## Interface

```
ProjectDocument(project, path=None)
  project -> Project            # read access for rendering
  path -> Optional[str]
  is_dirty -> bool
  subscribe(callback)           # callback() on every change

  # clips
  add_clip(clip)
  add_clips(clips)              # no-op + no notify on empty
  remove_last_clip() -> Optional[Clip]   # None + no notify when empty

  # angle
  set_secondary_angle(periods, angle)
  clear_secondary_angle()

  # categories
  set_categories(categories)

  # playlists
  new_playlist(name) -> Playlist
  delete_playlist(pl_id)
  add_clip_to_playlist(pl_id, clip_id)    # dedupe; notify only if added
  remove_clip_from_playlist(pl_id, clip_id)
  reorder_playlist(pl_id, clip_ids)
  clips_of(pl_id) -> List[Clip]

  # persistence
  save()                        # raises if no path; clears dirty
  save_as(path)
```

Every mutation calls a private `_changed()` → sets dirty, fires listeners once.

## Steps (each its own commit)

1. **`test_project_document.py` (red)** — Qt-free. Cover: each mutation sets `is_dirty` and
   fires the subscriber exactly once; `add_clips([])` and `remove_last_clip()`-on-empty are
   no-ops with no notify; `add_clip_to_playlist` dedupe path doesn't notify; `clips_of`
   filters missing ids; `save_as` then reload via `ProjectManager` round-trips and clears
   dirty.
2. **`core/project_document.py` (green)** — implement to pass.
3. **Migrate `MainWindow`** — hold `self._doc` instead of `_project`/`_project_path`/`_dirty`.
   `_load_project` builds the document; subscribe once with `_refresh_all`. Rewrite
   `_mark_out`, `_undo_last_clip`, `_import_timestamps`, `_new_playlist`,
   `_apply_secondary_angle`, `_manage_angles`, `_save_project`, `closeEvent`,
   `_package_project` to go through `self._doc`. `_on_present_requested` uses `doc.clips_of`.
   Keep video-not-found UI as-is.
4. **Migrate `ClipsPanel`** — add `add_clips_to_playlist_requested(pl_id, clip_ids)` and
   `delete_playlist_requested(pl_id)` signals; drop the direct `PlaylistBuilder` calls and
   local `_refresh_playlists()` writes. `MainWindow` wires the new signals to `self._doc`.
   Panel still renders from the project handed to `refresh()`.
5. **Migrate `TagManagerDialog`** — receive the document; edit a `copy.deepcopy` of
   `doc.project.categories`; on Done call `doc.set_categories(copy)`. Cancel discards.
6. **Migrate `AngleSyncDialog`** — receive the document; `_accept` calls
   `doc.set_secondary_angle(periods, angle)` instead of assigning `project.periods/angles`.
7. **Delete `core/playlist_builder.py`** and fold/port its tests into
   `test_project_document.py`. Update any remaining importers.
8. **Verify** — `python -m pytest`; confirm the document/model/manager suites pass. Qt smoke
   tests remain environmental (baseline "64 passed, 12 errors" in the sandbox).

## Impact on the other candidates

- **#5 (fold PlaylistBuilder)** — done as part of this work (steps 4, 7).
- **#2 (lift angle-building)** — now lands on a ready commit point: the dialog will call
  `doc.set_secondary_angle(*build_angle(...))`. Smaller and independent.
- **#3 (consolidate persistence)** — unaffected by this work and vice-versa: `doc.save`
  delegates through `ProjectManager`, so consolidating the on-disk format behind
  `ProjectManager` changes nothing the document or its callers see.
- **#4 (angle-lock module)** — independent; touches `PlayerWidget`, not the document.
