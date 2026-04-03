# VideoTagger

A Windows desktop application for tagging and reviewing sporting footage. Open a video, mark clips with keyboard shortcuts, build playlists, and present or export them.

---

## Features

- **Open video files** — `.mp4`, `.mov`, `.avi`, `.mkv`, `.m4v`
- **Tag clips** — press `I` to mark start, `O` to mark end; assign a category and label
- **Timeline view** — colour-coded clip markers with clickable seek
- **Tag Manager** — create/rename/delete categories and labels; save and load templates
- **Built-in AFL template** — Offence, Defence, Stoppages, General (with labels pre-filled)
- **Playlists** — build and reorder clip playlists; add clips via right-click context menu
- **Presentation mode** — full-screen playlist playback with HUD overlay, auto-advance between clips
- **Export** — cut clips to individual `.mp4` files and/or generate a CMX 3600 `.edl` reference file
- **Project files** — save/load `.vtp` project files (plain JSON) for easy team sharing

---

## Quick Start (pre-built .exe)

1. Download `VideoTagger.exe` from the `dist/` folder (or the latest release).
2. Double-click `VideoTagger.exe` — no installation required.

ffmpeg is bundled inside the exe and requires no separate download.

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `I` | Mark clip start (IN point) |
| `O` | Mark clip end (OUT point) — opens clip dialog |
| `Escape` | Cancel current clip mark |
| `Ctrl+Z` | Undo last clip |
| `Left / Right` | Step ±5 seconds |
| `Shift+Left / Right` | Step ±1 frame (~0.04 s) |
| `[` / `]` | Decrease / increase playback speed |
| `F11` | Toggle presentation mode (when in presentation window) |
| `Ctrl+N` | New project |
| `Ctrl+O` | Open project |
| `Ctrl+S` | Save project |

---

## Tagging Workflow

1. **File → New Project** — select a video file and optionally choose a tag template.
2. Click a label in the **Tag Panel** to pre-select it (optional).
3. Press `I` at the moment you want the clip to start.
4. Press `O` at the moment you want the clip to end — the **New Clip** dialog opens.
5. Confirm the category, label, and times, then click OK.
6. Repeat. Use `Ctrl+Z` to undo the last clip if needed.

---

## Exporting

Right-click a playlist in the **Playlists** tab and choose **Export**.

- **MP4 cut files** — each clip is exported as `{video_name}_{Category}_{Label}_{001}.mp4`
- **EDL file** — a CMX 3600 edit decision list for use in video editing software

Both options can be selected simultaneously.

---

## Presentation Mode

Right-click a playlist and choose **Present**. The window goes full-screen and plays each clip in order with a 1-second gap between them. A HUD overlay shows the playlist name, current category/label, and clip counter.

- Move the mouse to reveal the HUD controls.
- Use `Space`, `Left`, `Right` or the on-screen buttons to navigate.
- Press `Escape` or `F11` to exit.

---

## Project Files

Projects are saved as `.vtp` files (plain JSON). Share them with teammates — they just need the same video file accessible at the same path (or VideoTagger will prompt to locate it on open).

---

## Building from Source

### Prerequisites

- Python 3.11+
- [VLC media player](https://www.videolan.org/) installed (provides `libvlc.dll`)
- `ffmpeg.exe` on PATH or in the project root

### Install dependencies

```
pip install -r requirements.txt
```

### Run from source

```
python main.py
```

### Run tests

```
python -m pytest tests/
```

### Build .exe

Before building, place `ffmpeg.exe` in the project root (it will be embedded in the output exe):

```
# Download from https://www.gyan.dev/ffmpeg/builds/
# Extract ffmpeg.exe from ffmpeg-release-essentials.zip → bin/ffmpeg.exe
# Place it at: VideoAnalysis/ffmpeg.exe
```

Then run:

```
python build.py
```

Output: `dist/VideoTagger.exe` — fully self-contained, no separate ffmpeg needed.

---

## Tag Templates

Templates are JSON files listing categories and labels. The built-in **AFL** template covers common football actions. Custom templates can be created and saved via **Tags → Manage Tags → Save as Template** and are stored in `%APPDATA%\VideoTagger\templates\`.

---

## File Naming

Exported clips are named:

```
{video_filename}_{Category}_{Label}_{instance#}.mp4
```

Example: `afl_round5_Offence_Goal_001.mp4`
