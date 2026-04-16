# VideoTagger

A desktop application for tagging and reviewing sporting footage. Open a video, mark clips with keyboard shortcuts, build playlists, and present or export them.

---

## Download

Go to the [**Releases page**](https://github.com/mitch-mooney/video_tagger/releases) and download the latest version for your platform:

| Platform | File | Notes |
|----------|------|-------|
| Windows | `VideoTagger.exe` | Double-click to run — no install needed |
| macOS | `VideoTagger.dmg` | See macOS setup instructions below |

Both files are fully self-contained — ffmpeg is bundled, no separate download required.

---

## Windows — Quick Start

1. Download `VideoTagger.exe` from the [latest release](https://github.com/mitch-mooney/video_tagger/releases/latest).
2. Double-click `VideoTagger.exe` — no installation required.

---

## macOS — Quick Start

### 1. Install VideoTagger

1. Download `VideoTagger.dmg` from the [latest release](https://github.com/mitch-mooney/video_tagger/releases/latest).
2. Open the `.dmg` file and drag **VideoTagger** into your **Applications** folder.

### 2. Bypass the unsigned app warning

Because VideoTagger is not signed with a paid Apple Developer certificate, macOS will block it on first launch. There are two ways to get around this:

**Option A — Right-click method (easiest):**
1. Open **Finder** and go to **Applications**.
2. **Right-click** (or Control-click) `VideoTagger`.
3. Choose **Open** from the menu.
4. Click **Open** in the dialog that appears.

You only need to do this once — macOS remembers the exception.

**Option B — Terminal (one command):**

Open Terminal and run:
```bash
xattr -rd com.apple.quarantine /Applications/VideoTagger.app
```
Then double-click normally to launch.

---

## Features

- **Open video files** — `.mp4`, `.mov`, `.avi`, `.mkv`, `.m4v`
- **Multi-file projects** — load a match split across multiple files (e.g. 2 GB camera splits); VideoTagger merges them into one continuous timeline via FFmpeg automatically
- **Tag clips** — press `I` to mark start, `O` to mark end; assign a category and label
- **Timeline view** — colour-coded clip markers with clickable seek
- **Tag Manager** — create/rename/delete categories and labels; save and load templates
- **Built-in AFL template** — Offence, Defence, Stoppages, General (with labels pre-filled)
- **Playlists** — build and reorder clip playlists; add clips via right-click context menu
- **Presentation mode** — full-screen playlist playback with HUD overlay, drawing tools, auto-advance between clips
- **Export** — cut clips to individual `.mp4` files and/or generate a CMX 3600 `.edl` reference file
- **Project files** — save/load `.vtp` files (plain JSON) for easy team sharing, or package into a self-contained folder for portability

---

## Keyboard Shortcuts

### Main Window

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
| `Ctrl+N` | New project |
| `Ctrl+O` | Open project |
| `Ctrl+S` | Save project |

### Presentation Mode

| Key | Action |
|-----|--------|
| `Tab` | Next clip |
| `Shift+Tab` | Previous clip |
| `Space` | Pause / Play |
| `Left / Right` | Step ±5 seconds within clip |
| `,` / `.` | Step one frame back / forward |
| `[` / `]` | Decrease / increase playback speed |
| `D` | Toggle freehand drawing overlay |
| `C` | Clear drawing (in draw mode) |
| `K` | Cycle pen colour (in draw mode) |
| `N` | Pin / unpin clip notes |
| `Escape` / `F11` | Exit presentation |

---

## Tagging Workflow

1. **File → New Project** — select one or more video files (e.g. multiple 2 GB camera splits of the same match) and optionally choose a tag template. If multiple files are selected, VideoTagger merges them into a single playback file via FFmpeg before opening.
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

Right-click a playlist and choose **Present**. The window goes full-screen and plays each clip in order with a gap between them. A HUD overlay shows the playlist name, current category/label, and clip counter.

- Move the mouse to reveal the HUD controls.
- Use `Tab` / `Shift+Tab` to jump to the next or previous clip at any time.
- Use `Space` or the on-screen buttons to pause/play.
- Press `D` to enable the freehand drawing overlay — draw directly on the video with the mouse.
- Press `Escape` or `F11` to exit.

---

## Project Files

Projects are saved as `.vtp` files (plain JSON). Share them with teammates — they need the same video file (or merged file) accessible locally; VideoTagger will prompt to locate it on open.

**Packaging:** Use **File → Package Project...** to bundle the project file and video into a self-contained folder. Useful for archiving or sending to someone who doesn't have the match footage.

---

## Releasing a New Version

Push a version tag and GitHub Actions builds both platforms automatically:

```bash
git tag v1.1.0
git push origin v1.1.0
```

The workflow builds `VideoTagger.exe` (Windows) and `VideoTagger.dmg` (macOS) in parallel and attaches both to a GitHub Release. No manual building or file distribution needed.

---

## Building from Source

### Prerequisites

- Python 3.9+
- `ffmpeg` / `ffmpeg.exe` in the project root (embedded in the output binary)

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

### Build (Windows)

Download `ffmpeg.exe` from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) → `ffmpeg-release-essentials.zip` → extract `bin/ffmpeg.exe` into the project root, then:

```
python build.py
```

Output: `dist/VideoTagger.exe`

### Build (macOS)

```bash
brew install ffmpeg create-dmg
cp $(which ffmpeg) ./ffmpeg
python build.py
```

Output: `dist/VideoTagger.dmg`

---

## Tag Templates

Templates are JSON files listing categories and labels. The built-in **AFL** template covers common football actions. Custom templates can be created and saved via **Tags → Manage Tags → Save as Template**.

- **Windows:** `%APPDATA%\VideoTagger\templates\`
- **macOS:** `~/Library/Application Support/VideoTagger/templates/`

---

## File Naming

Exported clips are named:

```
{video_filename}_{Category}_{Label}_{instance#}.mp4
```

Example: `afl_round5_Offence_Goal_001.mp4`
