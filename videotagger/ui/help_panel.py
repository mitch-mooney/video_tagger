# videotagger/ui/help_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser

HELP_HTML = """
<html>
<head>
<style>
  body { font-family: 'Segoe UI Variable Text', 'Segoe UI', system-ui, sans-serif;
         font-size: 9pt; color: #e8eef6; background: #06090e;
         margin: 14px 18px; line-height: 1.75; }
  h2   { color: #15e6c4; font-size: 10.5pt; font-weight: 700;
         margin: 20px 0 6px 0; border-bottom: 1px solid #232d3d;
         padding-bottom: 5px; letter-spacing: 0.3px; }
  h3   { color: #7e90a8; font-size: 9pt; font-weight: 600;
         margin: 14px 0 4px 0; text-transform: uppercase;
         letter-spacing: 0.7px; font-size: 8pt; }
  p    { margin: 4px 0 10px 0; color: #7e90a8; }
  code { background: #161f2d; color: #5cf3da; padding: 1px 6px;
         border-radius: 4px; border: 1px solid #232d3d;
         font-family: 'Cascadia Mono', 'Cascadia Code', Consolas, monospace; font-size: 8pt; }
  table { border-collapse: collapse; width: 100%; margin: 8px 0 14px 0; }
  th   { background: #06090e; color: #4a5a70; text-align: left;
         padding: 6px 10px; border-bottom: 1px solid #232d3d;
         font-size: 7.5pt; letter-spacing: 1px; text-transform: uppercase;
         font-weight: 700; }
  td   { padding: 6px 10px; border-bottom: 1px solid #19212f; color: #7e90a8; }
  td:first-child { color: #15e6c4; font-family: 'Cascadia Mono', 'Cascadia Code', Consolas, monospace;
                   font-size: 8pt; white-space: nowrap; }
  tr:hover td { background: #161f2d; }
  .tip { background: #0c2320; border-left: 3px solid #15e6c4;
         padding: 8px 12px; margin: 10px 0; border-radius: 0 5px 5px 0;
         color: #9fb4ad; }
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
  <tr><td>+ / −</td><td>Zoom in / out (or scroll wheel over the video)</td></tr>
  <tr><td>0</td><td>Reset zoom to full frame</td></tr>
  <tr><td>V</td><td>Switch camera angle (when a second angle is loaded)</td></tr>
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
category. Click a clip marker to jump to its start time. Click blank space to seek.
If you've marked periods (see below), <code>Q1</code>–<code>Q4</code> dividers show where
each quarter begins.</p>

<h2>Periods (Quarters)</h2>
<p>Divide the match into periods so the timeline shows quarter dividers — handy for
navigation, and used by the dual-angle sync.</p>
<ol>
  <li>Go to <b>Video → Manage Periods</b>.</li>
  <li>Scrub the preview to the frame each period begins, select that period's row,
      and click <b>Set Start @ Playhead</b>. Add or remove rows for halves, etc.</li>
  <li>Click <b>OK</b> — the <code>Q1</code>–<code>Q4</code> dividers appear on the timeline.</li>
</ol>

<h2>Camera Angles</h2>
<p>Review the same match from two angles (e.g. behind-goals and broadcast) and switch
between them instantly during playback.</p>
<ol>
  <li>Go to <b>Video → Manage Angles</b> and add the second angle's video file(s).</li>
  <li>Mark where each period starts in both videos, then click <b>OK</b>.</li>
  <li>Press <code>V</code> while playing to switch angles — they stay locked together and
      re-sync at every period boundary.</li>
</ol>

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
