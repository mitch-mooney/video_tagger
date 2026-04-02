import os
import subprocess
from pathlib import Path
from typing import List
from videotagger.models.project import Clip, Project

def _ffmpeg_path() -> str:
    bundled = Path(__file__).parent.parent / "resources" / "ffmpeg.exe"
    if bundled.exists():
        return str(bundled)
    return "ffmpeg"

def build_clip_filename(video_path: str, category_name: str, label: str, instance: int) -> str:
    stem = Path(video_path).stem
    return f"{stem}_{category_name}_{label}_{instance:03d}.mp4"

def export_clip(clip: Clip, category_name: str, instance: int,
                video_path: str, output_dir: str) -> str:
    filename = build_clip_filename(video_path, category_name, clip.label, instance)
    output_path = os.path.join(output_dir, filename)
    duration = str(round(clip.end - clip.start, 6))
    cmd = [
        _ffmpeg_path(), "-y",
        "-ss", str(clip.start),
        "-i", video_path,
        "-t", duration,
        "-c", "copy",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")
    return output_path

def export_playlist_clips(playlist_clips: List[Clip], project: Project,
                          output_dir: str) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    cat_map = {c.id: c for c in project.categories}
    label_counts: dict = {}
    outputs = []
    for clip in playlist_clips:
        cat = cat_map.get(clip.category_id)
        cat_name = cat.name if cat else "Unknown"
        key = f"{cat_name}_{clip.label}"
        label_counts[key] = label_counts.get(key, 0) + 1
        out = export_clip(clip, cat_name, label_counts[key], project.video_path, output_dir)
        outputs.append(out)
    return outputs
