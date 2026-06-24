# Changelog

All notable changes to VideoTagger are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

## [v2.1.1] — 2026-06-22

### Added
- **Change the primary angle** — promote a synced secondary angle to the primary
  (canonical) timeline via **Video ▸ Manage Angles ▸ Make This Angle Primary**. Periods
  re-anchor and existing clips are remapped per-period, so you can (e.g.) start tagging a
  first-half-only video, then make a whole-match angle the primary and keep your clips. The
  old primary becomes the secondary angle.
- **Clear Second** button in Manage Angles to blank a sync point.

### Fixed
- **Angles that don't cover every period no longer corrupt timing.** A quarter an angle
  never recorded is treated as null instead of `0:00`: uncaptured starts are no longer
  fabricated as 0, out-of-order sync points (a start earlier than the period before it) are
  auto-nulled, the angle toggle goes inert where it has no footage, and **Make Primary**
  refuses to run when two periods share a start.

## [v2.1.0] — 2026-06-22

### Fixed
- **Blank video preview** in the Manage Periods / Manage Angles dialogs — the preview now
  plays briefly to decode the first frame before pausing, instead of pausing before the
  media has loaded (which left the surface black on Windows).

### Changed
- **Audio is now always stripped** from the project working video and all
  exports (`-an`). Merging source videos produces a video-only file, and both
  per-clip and merged-playlist exports are silent.

### Added
- **Manage Periods** — mark match periods (quarters/halves) on any project via
  **Video ▸ Manage Periods…** without needing a second camera angle. Scrub the preview,
  capture each period's start, and the timeline ribbon draws `Q1`–`Q4` dividers. The same
  period data feeds the dual-angle sync.
- **Broadcast Studio UI** — refined dark facelift: three-tier surface depth, a signature
  electric-teal accent with an amber "marking" signal, condensed display headers and tabular
  mono timecodes, category colour dots in the tags tree and clips table, period dividers on
  the timeline, visible focus rings, and a unified spacing scale. The team-colour accent
  (**Settings ▸ Team Color**) now applies consistently across the whole interface.
- **Dual camera angles with per-period sync** — load a second angle (e.g. broadcast
  vision alongside behind-goals) via **Video ▸ Manage Angles…**, mark where each
  quarter/period starts in both videos, then press **`V`** to switch angles instantly
  while playing. Both angles decode in lockstep (seamless switching, no reload) and
  re-sync at every period boundary, so a continuous recording and a per-quarter one stay
  aligned. Clips are shared across angles; existing single-angle projects are unaffected.
- **Live zoom & pan** in the main player and Presentation Mode — scroll wheel or
  `+` / `-` to zoom (centered on the cursor for the wheel), click-drag to pan, and
  `0` to reset to the full frame. Useful for inspecting a region of high-resolution
  (e.g. 4K) footage. Zoom persists while reviewing in the main player; in
  Presentation Mode it resets to the full frame at the start of each clip.

---

## [v2.0.1] — 2026-04-17

### Fixed
- **macOS build** — app icon converted from PNG to ICNS at CI build time; PyInstaller no longer rejects the icon on macOS
- **CI builds on master** — GitHub Actions now triggers a build on every push to `master` so failures are caught before tagging a release

---

## [v2.0.0] — 2026-04-17

### Added
- **Export: single merged file** — export an entire playlist as one concatenated `.mp4` via FFmpeg concat filter
- **Export: notes text file** — export a `.txt` summary of all clips with timestamps and notes
- **Export: burn notes overlay** — render clip notes as a yellow on-screen text overlay directly into exported `.mp4` files (individual clips and/or merged), styled to match Presentation Mode
- **v2.0 header badge** — version badge displayed in the application header

### Changed
- **Studio Dark UI redesign** — complete visual overhaul for v2.0:
  - Deeper void-black palette (`#060911` / `#080c12`) replacing flat navy
  - Underline tab navigation replacing boxy chrome tabs
  - Header: gradient background, monospace file label
  - Player controls: pill-shaped play button, Cascadia Code timecodes (42 px bar)
  - Shortcut bar: 3D key badges, condensed hints, dot MARKING indicator
  - Timeline: accent-coloured playhead with triangle cap, teal notes dots, clip highlight edges
  - Buttons, inputs, checkboxes, group boxes all refined
  - Help panel HTML updated to match new palette
- **Video backend** — replaced VLC (`python-vlc`) with Qt's native `QMediaPlayer` / `QtMultimedia` on both Windows and macOS; no longer requires a separate VLC installation
- **Export crash fix** — `Project.video_path` attribute reference corrected to `merged_video_path`

### Removed
- **Freehand drawing overlay** — annotation drawing in Presentation Mode removed (architecture incompatibility with DirectX video surface on Windows)
- **VLC dependency** — `python-vlc` and VLC media player are no longer required

---

## Installation

### Windows
1. Download **VideoTagger.exe** below.
2. Double-click to run — no installation required. FFmpeg is bundled.

### macOS
1. Download **VideoTagger.dmg** below.
2. Open the `.dmg` and drag **VideoTagger** into **Applications**.
3. First launch — bypass the Gatekeeper warning with one of:
   - **Right-click → Open → Open** in Finder (only needed once)
   - Or in Terminal: `xattr -rd com.apple.quarantine /Applications/VideoTagger.app`

---

## [v1.1.0] — 2026-04-02

### Added
- Multi-file project support — load a match split across multiple video files; VideoTagger merges them via FFmpeg into a single continuous timeline
- Presentation Mode — full-screen playlist playback with auto-advancing HUD, notes overlay, and keyboard navigation
- Import timestamps — bulk-create clips from a pasted timestamp list
- Package Project — bundle project file and merged video into a self-contained folder
- Tag templates — save and load category/label sets; built-in AFL template

### Changed
- Project file format updated to v2 model (`source_video_paths` + `merged_video_path`)

---

## [v1.0.0] — 2025-12-01

Initial release.

### Features
- Open video files (`.mp4`, `.mov`, `.avi`, `.mkv`, `.m4v`)
- Mark clips with `I` / `O` keyboard shortcuts
- Assign category, label, and notes per clip
- Colour-coded timeline with clickable seek
- Tag Manager with category colour picker
- Playlists with right-click context menu
- Export clips as individual `.mp4` files and/or CMX 3600 `.edl`
- Save / load `.vtp` project files (plain JSON)
- Team accent colour picker
