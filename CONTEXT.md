# CONTEXT — VideoTagger domain glossary

The shared, ubiquitous language for the `videotagger/` codebase. Names here are the
canonical terms; use them in code, tests, and architecture discussion.

## Domain entities

- **Project** — the root aggregate (`models/project.py`): the merged/source video paths,
  plus its clips, playlists, categories, periods and angles. A plain dataclass — it holds
  data and invariants, not orchestration.
- **Clip** — a marked `[start, end)` span on the canonical timeline with a category, label
  and notes.
- **Playlist** — an ordered selection of clips (by id), for export or presentation.
- **Category / Label** — the tag vocabulary. A category has a colour and a list of labels.
- **Period** — a match segment (quarter/half) anchored on the primary/canonical timeline
  (`primary_start`).
- **Video angle** — an additional camera angle synced onto the canonical timeline per
  period. The primary angle *is* the canonical timeline. An angle only **covers** the
  periods it has a sync point for; where it doesn't (e.g. a quarter it never recorded), it
  has *no* sync entry (null, never `0:00`) and is treated as unavailable — the toggle goes
  inert there and playback stays on the primary (`angle_sync.angle_covers`).
- **Promote to primary** — swapping the canonical timeline onto a secondary angle:
  periods re-anchor to the angle's start times, clip times are remapped per-period, and
  the old primary becomes a secondary angle. Requires every period to be synced in the
  target angle (then every clip is remappable). Pure: `angle_sync.promote_to_primary`.

## Application objects

- **Project document** (`core/project_document.py`, `ProjectDocument`) — the live editing
  object. It owns the in-memory **Project**, its file path, and the dirty flag, and is the
  **single write path** for every project mutation (clips, playlists, categories, angle).
  Each mutation sets dirty and fires one coarse `changed` notification; reads go through
  `doc.project`. It delegates bytes to `ProjectManager` (`save`/`save_as`). Pure Python —
  no Qt — so edits are testable headless. `MainWindow` is the only subscriber; it bridges
  `changed` to a refresh-all of the panels.

- **Angle mapping** (`core/angle_sync.py`) — pure functions mapping a canonical time onto a
  secondary angle's video time, per period. No Qt.

- **Tagging engine** (`core/tagging_engine.py`) — the mark-in/mark-out state machine.

## Seams worth naming

- The **document write seam**: callers never mutate `project.*` directly; they call
  `ProjectDocument` methods (or, for widgets, emit request signals that `MainWindow` routes
  to the document). This is where dirty-tracking lives.
- The **persistence seam**: `ProjectManager.save/load` is the only code that knows the
  on-disk format.
