# VideoTagger

A desktop application for tagging and reviewing sporting footage. Open a video, mark clips with keyboard shortcuts, build playlists, and present or export them.

**Current release: v2.1.0**

---

## Download

Go to the [**Releases page**](https://github.com/mitch-mooney/video_tagger/releases) and download the latest version for your platform:

| Platform | File | Notes |
|----------|------|-------|
| Windows | `VideoTagger.exe` | Double-click to run — no install needed |
| macOS | `VideoTagger.app` | See macOS setup instructions below |

Both files are fully self-contained — FFmpeg is bundled, no separate download required.

---

## Windows — Quick Start

1. Download `VideoTagger.exe` from the [latest release](https://github.com/mitch-mooney/video_tagger/releases/latest).
2. Double-click `VideoTagger.exe` — no installation required.

---

## macOS — Quick Start

### 1. Install VideoTagger

1. Download `VideoTagger.app` from the [latest release](https://github.com/mitch-mooney/video_tagger/releases/latest).
2. Drag **VideoTagger** into your **Applications** folder.

### 2. Bypass the unsigned app warning

Because VideoTagger is not signed with a paid Apple Developer certificate, macOS will block it on first launch. There are two ways to get around this:

**Option A — Right-click method (easiest):**
1. Open **Finder** and go to **Applications**.
2. **Right-click** (or Control-click) `VideoTagger`.
3. Choose **Open** from the menu.
4. Click **Open** in the dialog that appears.

You only need to do this once — macOS remembers the exception.

**Option B — Terminal (one command):**

```bash
xattr -rd com.apple.quarantine /Applications/VideoTagger.app
```

Then double-click normally to launch.

---

## Features

- **Open video files** — `.mp4`, `.mov`, `.avi`, `.mkv`, `.m4v`
- **Multi-file projects** — load a match split across multiple files; VideoTagger merges them into one continuous timeline via FFmpeg automatically
- **Dual camera angles** — load a second angle (e.g. broadcast vision alongside behind-goals), sync them at each quarter/period start, and switch instantly with `V` while playing — both angles decode in lockstep for seamless switching
- **Tag clips** — press `I` to mark start, `O` to mark end; assign a category, label, and optional notes
- **Timeline view** — colour-coded clip markers with clickable seek and notes indicators
- **Match periods** — mark quarter/half starts via **Video → Manage Periods** to show `Q1`–`Q4` dividers on the timeline
- **Tag Manager** — create, rename, delete categories and labels; save and load templates
- **Built-in AFL template** — Offence, Defence, Stoppages, General (with labels pre-filled)
- **Playlists** — build clip playlists; add clips via right-click context menu
- **Presentation mode** — full-screen playlist playback with auto-advancing HUD, pin/unpin notes overlay
- **Export** — individual clip files, single merged file, EDL reference, and notes text file; optional notes burn-in overlay on video
- **Team colour** — customise the accent colour via **Settings → Team Color**
- **Project files** — save/load `.vtp` files (plain JSON); package into a self-contained folder for easy sharing

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
| `Left` / `Right` | Step ±5 seconds |
| `Shift+Left` / `Shift+Right` | Step ±1 frame (~0.04 s) |
| `[` / `]` | Decrease / increase playback speed |
| `+` / `-` | Zoom in / out (or scroll wheel over the video) |
| `0` | Reset zoom to full frame |
| Click + drag | Pan the zoomed view |
| `V` | Switch camera angle (when a second angle is loaded) |
| `Ctrl+N` | New project |
| `Ctrl+O` | Open project |
| `Ctrl+S` | Save project |

### Presentation Mode

| Key | Action |
|-----|--------|
| `Tab` | Next clip |
| `Shift+Tab` | Previous clip |
| `Space` | Pause / Play |
| `Left` / `Right` | Step ±5 seconds within clip |
| `,` / `.` | Step one frame back / forward |
| `[` / `]` | Decrease / increase playback speed |
| `+` / `-` | Zoom in / out (or scroll wheel over the video) |
| `0` | Reset zoom to full frame |
| Click + drag | Pan the zoomed view |
| `N` | Pin / unpin clip notes overlay |
| `Escape` / `F11` | Exit presentation |

---

## Tagging Workflow

1. **File → New Project** — select one or more video files and optionally choose a tag template. If multiple files are selected, VideoTagger merges them into a single playback file via FFmpeg.
2. Click a label in the **Tag Panel** to pre-select it (optional).
3. Press `I` at the moment you want the clip to start.
4. Press `O` at the moment you want the clip to end — the **New Clip** dialog opens.
5. Confirm the category, label, optional notes, and times, then click OK.
6. Repeat. Use `Ctrl+Z` to undo the last clip if needed.
7. Press `Ctrl+S` to save your project.

---

## Playlists

1. In the **Playlists** tab, click **New Playlist** and give it a name.
2. Switch to the **Clips** tab, right-click any clip, and choose **Add to Playlist**.
3. Right-click a playlist to **Present** or **Export** it.

---

## Presentation Mode

Right-click a playlist and choose **Present**. The window goes full-screen and plays each clip in order with an auto-advance gap between them.

- Move the mouse to reveal the HUD controls (it auto-hides after 3 seconds).
- Use `Tab` / `Shift+Tab` to jump to the next or previous clip at any time.
- Use `Space` or the on-screen buttons to pause/play.
- Press `N` to pin the current clip's notes on screen.
- Press `Escape` or `F11` to exit.

---

## Periods (Quarters)

Divide the match into periods so the timeline shows `Q1`–`Q4` dividers — useful for navigation,
and reused by the dual-angle sync.

1. With a project open, go to **Video → Manage Periods…**.
2. The dialog opens with `Q1`–`Q4` pre-filled and a scrubbable preview. Scrub to the exact
   frame each period begins, select that period's row, and click **Set Start @ Playhead**.
   Add or remove rows for halves or extra periods.
3. Click **OK** — the dividers appear on the timeline immediately. Save to keep them in the `.vtp`.

Works on any project — no second camera angle required.

---

## Camera Angles

Review the same match from two angles (e.g. behind-goals and broadcast vision) and switch
between them instantly while playing.

1. With a project open, go to **Video → Manage Angles…**.
2. Add the second angle's video file(s) and click **Load / Merge Angle** (multiple files are
   merged just like the primary, e.g. one file per quarter).
3. The two videos appear side by side. For each period row (Q1–Q4 by default; add/remove/rename
   as needed), scrub each preview to the exact frame the period begins, select the row, and click
   **Set Primary @ Playhead** / **Set Second @ Playhead**.
4. Click **OK**. Back in the main window, press **`V`** to switch angles — both play in lockstep
   and re-sync at every period boundary, so a continuous recording and a per-quarter one stay
   aligned. Clips are shared across angles. Save to keep the sync points in the `.vtp`.

---

## Exporting

Right-click a playlist in the **Playlists** tab and choose **Export**. The export dialog offers four independent options — select any combination:

|--------|--------|-------|
| **Individual clip files** | One `.mp4` per clip | Named `{video}_{Category}_{Label}_{001}.mp4`; stream-copied (fast) |
| **Single merged file** | One `.mp4` for the whole playlist | All clips concatenated in order via FFmpeg |
| **EDL reference file** | `.edl` | CMX 3600 format for use in editing software |
| **Notes text file** | `.txt` | Each clip with its category, label, timestamps, and notes |

**Burn notes onto video** — check this option to render each clip's notes as a yellow on-screen text overlay in the exported `.mp4` file(s). The overlay style matches what is shown in Presentation Mode. Note: this requires re-encoding and is slower than stream-copy export.

---

## Project Files

Projects are saved as `.vtp` files (plain JSON). Share them with teammates — they need the same video file accessible locally; VideoTagger will prompt to locate it on open.

**Packaging:** Use **File → Package Project...** to bundle the project file and merged video into a single self-contained folder. Useful for archiving completed matches or sending to someone who doesn't have the footage.

---

## Releasing a New Version

Push a version tag and GitHub Actions builds both platforms automatically:

```bash
git tag v2.1.0
git push origin v2.1.0
```

The workflow builds `VideoTagger.exe` (Windows) and `VideoTagger.app` / `.dmg` (macOS) in parallel and attaches both to a GitHub Release.

---

## Building from Source

### Prerequisites

- Python 3.9+
- `ffmpeg` / `ffmpeg.exe` in the project root (embedded in the output binary)

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run from source

```bash
python main.py
```

### Run tests

```bash
python -m pytest tests/
```

### Build (Windows)

Download `ffmpeg.exe` from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) → `ffmpeg-release-essentials.zip` → extract `bin/ffmpeg.exe` into the project root, then:

```bash
pyinstaller VideoTagger.spec
```

Output: `dist/VideoTagger.exe`

### Build (macOS)

```bash
brew install ffmpeg create-dmg
cp $(which ffmpeg) ./ffmpeg
pyinstaller VideoTagger.spec
```

Output: `dist/VideoTagger.app` / `dist/VideoTagger.dmg`

---

## Tag Templates

Templates are JSON files listing categories and labels. The built-in **AFL** template covers common football actions. Custom templates can be created and saved via **Tags → Manage Tags → Save as Template**.

Template locations:
- **Windows:** `%APPDATA%\VideoTagger\templates\`
- **macOS:** `~/Library/Application Support/VideoTagger/templates/`

---

## File Naming

Exported individual clips are named:

```
{video_filename}_{Category}_{Label}_{instance#}.mp4
```

Example: `afl_round5_Offence_Goal_001.mp4`

The merged playlist export is named:

```
{playlist_name}.mp4
```
