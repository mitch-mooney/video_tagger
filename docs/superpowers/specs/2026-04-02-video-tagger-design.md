# Video Tagger — Design Spec
**Date:** 2026-04-02
**Status:** Approved

---

## Overview

A Windows desktop application (`.exe`) for tagging sporting video footage. Users open a video file, mark clips with categorised labels, build playlists from those clips, and export playlists as cut video files or reference files. Designed for a small team (e.g., coaching staff) who share a video file and a `.vtp` project file.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| UI framework | PyQt6 |
| Video playback | libVLC (via python-vlc) |
| Clip export | ffmpeg (bundled binary, via ffmpeg-python) |
| Packaging | PyInstaller (single `.exe`) |
| Settings/templates | JSON files in `%APPDATA%\VideoTagger\` |

---

## Architecture

Four layers:

1. **UI Layer (PyQt6)** — main window, video player widget (embedded libVLC), timeline panel, tag manager dialog, clips list, playlist panel, export dialog
2. **Core Logic** — tagging engine (clip creation, start/end marking state machine), playlist builder, keyboard shortcut handler
3. **Data Layer** — project file manager (reads/writes `.vtp` JSON files), template manager (reads/writes named templates from `%APPDATA%\VideoTagger\templates\`)
4. **Export Layer** — ffmpeg wrapper for cutting clips to `.mp4`; EDL writer for playlist reference files

---

## UI Layout

**Layout B — Large player top, timeline middle, tags + clips bottom.**

```
┌─────────────────────────────────────────────────────┐
│                  VIDEO PLAYER                       │
│              (large, dominant area)                 │
│         00:12:34 / 01:28:00  [controls]             │
├─────────────────────────────────────────────────────┤
│  TIMELINE  ████░░░░████░░░░░░███░░░░░░░░░░░░░░░░░  │
│            (colour-coded clip markers)              │
├────────────────────────┬────────────────────────────┤
│  TAGS                  │  CLIPS (12)                │
│  ▶ Offence             │  Goal     12:34–12:41      │
│  ▶ Defence             │  Tackle   23:10–23:18      │
│  ▶ Stoppages           │  Behind   45:02–45:09      │
└────────────────────────┴────────────────────────────┘
```

Panels are resizable. The bottom row can be collapsed to maximise video area.

The **right bottom panel** has two tabs:
- **Clips** — all tagged clips for this project (sortable by time, category, or label)
- **Playlists** — named playlists; click a playlist to filter the clips list to only those clips

The **left bottom panel** shows the tag category/label tree used for quick reference while tagging (clicking a label pre-selects it in the next clip dialog).

---

## Project File Format

Project files use the `.vtp` extension (Video Tagging Project) and are plain JSON.

```json
{
  "version": 1,
  "video_path": "C:/footage/afl_round5.mp4",
  "categories": [
    {
      "id": "uuid",
      "name": "Offence",
      "color": "#e94560",
      "labels": ["Goal", "Behind", "Handball", "Kick", "Mark"]
    },
    {
      "id": "uuid",
      "name": "Defence",
      "color": "#4ade80",
      "labels": ["Tackle", "Spoil", "Intercept", "Pressure"]
    },
    {
      "id": "uuid",
      "name": "Stoppages",
      "color": "#facc15",
      "labels": ["Ball-up", "Boundary Throw-in"]
    }
  ],
  "clips": [
    {
      "id": "uuid",
      "category_id": "uuid",
      "label": "Goal",
      "start": 754.2,
      "end": 761.8,
      "notes": "Strong snap from 40m"
    }
  ],
  "playlists": [
    {
      "id": "uuid",
      "name": "Goals Round 5",
      "clip_ids": ["uuid1", "uuid2"]
    }
  ]
}
```

- Times stored as seconds (float) for precision
- Video path is stored as-is; teammates update it to their local path
- File is human-readable and can be version-controlled

---

## Tag Management

A **Tag Manager dialog** is accessible from the menu at any time (not just on project creation).

**Features:**
- Add / rename / delete categories (each with a colour)
- Add / rename / delete labels within a category
- Reorder categories and labels via drag-and-drop
- **Save as Template** — saves the current category/label setup as a named `.json` template to `%APPDATA%\VideoTagger\templates\`
- **Load Template** — replaces current categories/labels with a saved template (with confirmation if clips exist)

**On first new project:** prompts user to load a template or start blank. A built-in "AFL" template is included with the app:

| Category | Labels |
|----------|--------|
| Offence | Goal, Behind, Handball, Kick, Mark, Shot at Goal |
| Defence | Tackle, Spoil, Intercept, Pressure Act, Smother |
| Stoppages | Ball-up, Boundary Throw-in, Kick-in |
| General | Error, Highlight |

---

## Tagging Workflow

1. Open project (new or existing `.vtp`)
2. Video loads and plays; timeline shows existing clips colour-coded by category
3. **Mark a clip:**
   - Press `I` while playing to set the start point (playback continues)
   - Press `O` to set the end point — a dialog opens to assign category + label + optional note
   - Alternatively, enter start/end times manually in the dialog
   - Confirm → clip appears on the timeline and clips list
4. Click any clip in the timeline or list to jump to it and preview
5. Right-click a clip → Edit, Delete, or Add to Playlist
6. **Build playlists** — drag clips into a named playlist in the playlist panel, or multi-select + right-click → Add to Playlist

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `I` | Mark clip start |
| `O` | Mark clip end |
| `←` / `→` | Step ±5 seconds |
| `Shift+←/→` | Step ±1 frame |
| `[` / `]` | Decrease / increase playback speed |
| `Escape` | Cancel in-progress clip mark / Exit presentation mode |
| `Ctrl+S` | Save project |
| `Ctrl+Z` | Undo last clip |
| `F11` | Enter / exit presentation mode |

---

## Presentation Mode

A full-screen playback mode for reviewing a playlist with a group (e.g., team film session).

**Entering presentation mode:**
- Right-click a playlist → **Present Playlist**, or
- Select a playlist and press `F11`

**Behaviour:**
- App goes full-screen, all UI chrome hidden
- Plays through each clip in the playlist sequentially with a brief 1-second black gap between clips
- **Minimal HUD overlay** (fades out after 3 seconds of inactivity, reappears on mouse move):
  - Top-left: playlist name
  - Bottom-left: clip label and category (e.g., "Offence — Goal")
  - Bottom-right: clip counter (e.g., "3 / 12")
  - Centre-bottom: play/pause, previous clip, next clip buttons
- Auto-advances to next clip on completion; pauses after the last clip
- **Exiting:** press `Escape` or `F11` to return to normal view

**Keyboard shortcuts in presentation mode:**

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `←` / `→` | Previous / next clip |
| `Escape` / `F11` | Exit presentation mode |

---

## Export

Accessible via right-click on a playlist → **Export Playlist**.

### Export dialog options:

1. **Format:**
   - **Cut video files (.mp4)** — each clip extracted as a separate file using ffmpeg; output to a selected folder
   - **EDL file** — standard Edit Decision List referencing the original video with timecodes (importable into DaVinci Resolve, Premiere Pro, etc.)
   - **Both** — produces cut files AND an EDL in one operation

2. **File naming:** auto-named as `{video_filename}_{Category}_{Label}_{instance#}` (e.g., `afl_round5_Offence_Goal_001.mp4`). Instance number is a zero-padded sequential count per label across the playlist (001, 002, ...). The naming pattern is shown in the export dialog and can be overridden manually.

3. ffmpeg is bundled inside the `.exe` — no external dependencies for teammates

---

## Packaging

- **PyInstaller** bundles Python runtime, PyQt6, libVLC, and ffmpeg binary into a single `.exe`
- **No installer required** — double-click to run
- **Target bundle size:** ~150–200 MB
- **Persistent data** stored in `%APPDATA%\VideoTagger\`:
  - `templates/` — saved tag templates
  - `settings.json` — window layout, recent files, preferences
- `.vtp` files are associated with the app on first launch (optional, with user prompt)

---

## Error Handling

- If video file is missing on project open: prompt user to locate it (file picker), update path in project
- If ffmpeg export fails: show error with ffmpeg stderr output; partial exports are placed in a `_partial/` subfolder
- Unsaved changes on close: standard "Save before closing?" dialog
- Corrupt `.vtp` file: show parse error with line info, offer to open a backup if one exists

---

## Out of Scope (v1)

- Real-time collaboration / sync
- Cloud storage or remote video streaming
- Frame-accurate waveform audio display
- Drawing/annotation overlays on video
- Auto-tagging via computer vision
