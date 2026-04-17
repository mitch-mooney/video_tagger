# Changelog

All notable changes to VideoTagger are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
