# videotagger/ui/help_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser

HELP_HTML = """
<html>
<head>
<style>
  body { font-family: 'Segoe UI', sans-serif; font-size: 9pt;
         color: #dde3ea; background: #090d12; margin: 12px 16px; line-height: 1.7; }
  h2   { color: #00b09b; font-size: 11pt; margin: 18px 0 6px 0;
         border-bottom: 1px solid #1e2a38; padding-bottom: 4px; }
  h3   { color: #7dcfc8; font-size: 9.5pt; margin: 14px 0 4px 0; }
  p    { margin: 4px 0 8px 0; color: #b8c6d4; }
  code { background: #1e2a38; color: #00d4b8; padding: 1px 5px;
         border-radius: 3px; font-family: Consolas, monospace; font-size: 8.5pt; }
  table { border-collapse: collapse; width: 100%; margin: 8px 0; }
  th   { background: #090d12; color: #7d8fa3; text-align: left;
         padding: 5px 10px; border-bottom: 1px solid #1e2a38;
         font-size: 8pt; letter-spacing: 0.6px; text-transform: uppercase; }
  td   { padding: 5px 10px; border-bottom: 1px solid #1a2434; color: #b8c6d4; }
  td:first-child { color: #00b09b; font-family: Consolas, monospace;
                   font-size: 8.5pt; white-space: nowrap; }
  tr:hover td { background: #1a2b3c; }
  .tip { background: #0f3460; border-left: 3px solid #00b09b;
         padding: 6px 10px; margin: 8px 0; border-radius: 0 4px 4px 0; }
</style>
</head>
<body>

<h2>Getting Started</h2>
<p>VideoTagger lets you mark clips in sporting footage, organise them into playlists,
and export or present them to your team.</p>

<ol>
  <li>Go to <b>File → New Project</b> and select your video file.</li>
  <li>Optionally choose a tag template (e.g. <em>AFL</em>) to pre-load categories.</li>
  <li>The video will begin playing. Use the Tag panel on the left to pre-select a label.</li>
  <li>Press <code>I</code> to mark the start of a clip, then <code>O</code> to mark the end.</li>
  <li>Confirm the category, label and times in the dialog that appears.</li>
  <li>Press <b>Ctrl+S</b> to save your project as a <code>.vtp</code> file.</li>
</ol>

<h2>Keyboard Shortcuts</h2>
<table>
  <tr><th>Key</th><th>Action</th></tr>
  <tr><td>Space</td><td>Play / Pause</td></tr>
  <tr><td>I</td><td>Mark clip start (IN point)</td></tr>
  <tr><td>O</td><td>Mark clip end (OUT point) — opens clip dialog</td></tr>
  <tr><td>Escape</td><td>Cancel current clip mark</td></tr>
  <tr><td>Ctrl+Z</td><td>Undo last clip</td></tr>
  <tr><td>Left / Right</td><td>Step ±5 seconds</td></tr>
  <tr><td>Shift+Left / Right</td><td>Step ±1 frame (~0.04 s)</td></tr>
  <tr><td>[ / ]</td><td>Decrease / increase playback speed</td></tr>
  <tr><td>Ctrl+N</td><td>New project</td></tr>
  <tr><td>Ctrl+O</td><td>Open project</td></tr>
  <tr><td>Ctrl+S</td><td>Save project</td></tr>
</table>

<h2>Tagging Workflow</h2>
<h3>Pre-selecting a label</h3>
<p>Click a label in the <b>Tags</b> panel before pressing <code>I</code>. The label will be
pre-filled in the clip dialog so you can confirm with one click.</p>

<h3>Editing clip times manually</h3>
<p>In the New Clip dialog, use the <b>Start</b> and <b>End</b> spin boxes to fine-tune times
to the nearest 0.01 second.</p>

<h3>Timeline</h3>
<p>The coloured bar below the player shows all your clips. Each colour corresponds to a
category. Click a clip marker to jump to its start time. Click blank space to seek.</p>

<h2>Playlists</h2>
<p>Playlists let you group clips for presentation or export.</p>
<ol>
  <li>Go to the <b>Playlists</b> tab and right-click → <em>New Playlist</em>,
      or right-click a clip and choose <em>Add to playlist</em>.</li>
  <li>Right-click a playlist to <b>Present</b> or <b>Export</b>.</li>
</ol>

<h2>Presentation Mode</h2>
<p>Right-click a playlist → <b>Present Playlist</b>. The window goes full-screen and plays
each clip in order with a 1-second gap.</p>
<div class="tip">Move the mouse to reveal HUD controls. Press <code>Escape</code> or
<code>F11</code> to exit.</div>
<table>
  <tr><th>Key</th><th>Action</th></tr>
  <tr><td>Space</td><td>Play / Pause</td></tr>
  <tr><td>Left / Right</td><td>Previous / Next clip</td></tr>
  <tr><td>Escape or F11</td><td>Exit presentation</td></tr>
</table>

<h2>Exporting</h2>
<p>Right-click a playlist → <b>Export Playlist</b>. Choose one or both formats:</p>
<ul>
  <li><b>MP4 cut files</b> — each clip saved as
      <code>{video}_{Category}_{Label}_{001}.mp4</code></li>
  <li><b>EDL file</b> — a CMX 3600 edit decision list for video editing software</li>
</ul>

<h2>Tag Manager</h2>
<p>Go to <b>Tags → Manage Tags</b> to add, rename or delete categories and labels,
change category colours, and save or load templates.</p>
<div class="tip">The built-in <b>AFL</b> template includes Offence, Defence, Stoppages
and General categories with common labels pre-filled.</div>

<h2>Sharing Projects</h2>
<p>Project files (<code>.vtp</code>) are plain JSON — share them with teammates who have
the same video file. If the video path has changed, VideoTagger will prompt you to
locate it on open.</p>

</body>
</html>
"""


class HelpPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setHtml(HELP_HTML)
        layout.addWidget(browser)
