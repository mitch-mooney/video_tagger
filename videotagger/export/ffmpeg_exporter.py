import os
import subprocess
from pathlib import Path
from typing import List
from videotagger.models.project import Clip, Project


def _ffmpeg_path() -> str:
    import sys, shutil
    name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    if getattr(sys, "frozen", False):
        meipass = Path(sys._MEIPASS) / name
        if meipass.exists():
            return str(meipass)
    bundled = Path(__file__).parent.parent / "resources" / name
    if bundled.exists():
        return str(bundled)
    on_path = shutil.which("ffmpeg")
    if on_path:
        return on_path
    return "ffmpeg"


def _escape_drawtext(text: str) -> str:
    """Escape text for use in an FFmpeg drawtext filter value."""
    for ch, esc in [
        ("\\", "\\\\"), ("'", "\\'"), (":", "\\:"),
        ("\n", "\\n"), ("[", "\\["), ("]", "\\]"), (",", "\\,"),
    ]:
        text = text.replace(ch, esc)
    return text


def _drawtext_filter(text: str, enable_expr: str = "") -> str:
    """Build a drawtext filter string styled like the presentation HUD."""
    escaped = _escape_drawtext(text)
    f = (
        f"drawtext=text='{escaped}'"
        ":fontcolor=0xFFE066:fontsize=24"
        ":box=1:boxcolor=0x000000@0.73:boxborderw=8"
        ":x=20:y=h-th-40"
    )
    if enable_expr:
        f += f":enable='{enable_expr}'"
    return f


def build_clip_filename(video_path: str, category_name: str, label: str, instance: int) -> str:
    stem = Path(video_path).stem
    return f"{stem}_{category_name}_{label}_{instance:03d}.mp4"


def export_clip(clip: Clip, category_name: str, instance: int,
                video_path: str, output_dir: str, burn_notes: bool = False) -> str:
    filename = build_clip_filename(video_path, category_name, clip.label, instance)
    output_path = os.path.join(output_dir, filename)
    duration = str(round(clip.end - clip.start, 6))
    notes = (clip.notes or "").strip()
    cmd = [_ffmpeg_path(), "-y", "-ss", str(clip.start), "-i", video_path, "-t", duration]
    if burn_notes and notes:
        cmd += ["-vf", _drawtext_filter(notes)]
    else:
        cmd += ["-c", "copy"]
    cmd.append(output_path)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")
    return output_path


def export_playlist_clips(playlist_clips: List[Clip], project: Project,
                          output_dir: str, burn_notes: bool = False) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    cat_map = {c.id: c for c in project.categories}
    label_counts: dict = {}
    outputs = []
    for clip in playlist_clips:
        cat = cat_map.get(clip.category_id)
        cat_name = cat.name if cat else "Unknown"
        key = f"{cat_name}_{clip.label}"
        label_counts[key] = label_counts.get(key, 0) + 1
        out = export_clip(
            clip, cat_name, label_counts[key],
            project.merged_video_path, output_dir, burn_notes,
        )
        outputs.append(out)
    return outputs


def export_playlist_merged(playlist_clips: List[Clip], project: Project,
                           output_path: str, burn_notes: bool = False) -> str:
    """Concatenate all playlist clips into a single file via FFmpeg concat filter."""
    if not playlist_clips:
        raise RuntimeError("No clips to export.")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    filter_parts = []
    stream_labels = []
    for i, clip in enumerate(playlist_clips):
        filter_parts.append(
            f"[0:v]trim=start={clip.start}:end={clip.end},setpts=PTS-STARTPTS[v{i}];"
            f"[0:a]atrim=start={clip.start}:end={clip.end},asetpts=PTS-STARTPTS[a{i}]"
        )
        stream_labels.append(f"[v{i}][a{i}]")

    n = len(playlist_clips)
    concat_str = "".join(stream_labels) + f"concat=n={n}:v=1:a=1[outv][outa]"

    # Build per-clip drawtext filters timed to their position in the merged output.
    notes_filters = []
    if burn_notes:
        t = 0.0
        for clip in playlist_clips:
            duration = clip.end - clip.start
            notes = (clip.notes or "").strip()
            if notes:
                notes_filters.append(
                    _drawtext_filter(notes, f"between(t,{t:.3f},{t + duration:.3f})")
                )
            t += duration

    if notes_filters:
        filter_complex = (
            ";".join(filter_parts) + ";" + concat_str + ";" +
            "[outv]" + ",".join(notes_filters) + "[finalv]"
        )
        video_map = "[finalv]"
    else:
        filter_complex = ";".join(filter_parts) + ";" + concat_str
        video_map = "[outv]"

    cmd = [
        _ffmpeg_path(), "-y", "-i", project.merged_video_path,
        "-filter_complex", filter_complex,
        "-map", video_map, "-map", "[outa]",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")
    return output_path
