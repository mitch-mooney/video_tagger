from typing import List
from videotagger.models.project import Clip, Project

def seconds_to_timecode(seconds: float, fps: int = 25) -> str:
    total_frames = int(round(seconds * fps))
    frames = total_frames % fps
    secs = (total_frames // fps) % 60
    mins = (total_frames // (fps * 60)) % 60
    hours = total_frames // (fps * 3600)
    return f"{hours:02d}:{mins:02d}:{secs:02d}:{frames:02d}"

def write_edl(playlist_name: str, clips: List[Clip], project: Project,
              output_path: str, fps: int = 25) -> None:
    cat_map = {c.id: c for c in project.categories}
    lines = [f"TITLE: {playlist_name}", "FCM: NON-DROP FRAME", ""]
    rec_pos = 0.0
    for i, clip in enumerate(clips, 1):
        cat = cat_map.get(clip.category_id)
        cat_name = cat.name if cat else "Unknown"
        duration = clip.end - clip.start
        src_in = seconds_to_timecode(clip.start, fps)
        src_out = seconds_to_timecode(clip.end, fps)
        rec_in = seconds_to_timecode(rec_pos, fps)
        rec_out = seconds_to_timecode(rec_pos + duration, fps)
        rec_pos += duration
        lines.append(
            f"{i:03d}  AX       V     C        {src_in} {src_out} {rec_in} {rec_out}"
        )
        lines.append(f"* FROM CLIP NAME: {cat_name} - {clip.label}")
        if clip.notes:
            lines.append(f"* COMMENT: {clip.notes}")
        lines.append("")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
