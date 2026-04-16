import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from videotagger.models.project import Category, Clip, Project
from videotagger.export.ffmpeg_exporter import (
    build_clip_filename, export_clip, export_playlist_clips
)

def test_build_clip_filename():
    assert build_clip_filename("C:/footage/afl_round5.mp4", "Offence", "Goal", 1) \
        == "afl_round5_Offence_Goal_001.mp4"
    assert build_clip_filename("C:/footage/afl_round5.mp4", "Defence", "Tackle", 12) \
        == "afl_round5_Defence_Tackle_012.mp4"

def test_export_clip_calls_ffmpeg(tmp_path):
    cat = Category(id="cat1", name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(id="c1", category_id="cat1", label="Goal", start=10.0, end=17.0)
    proj = Project(source_video_paths=["video.mp4"], merged_video_path="video.mp4",
                   categories=[cat], clips=[clip])
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("videotagger.export.ffmpeg_exporter.subprocess.run", return_value=mock_result) as mock_run:
        output = export_clip(clip, "Offence", 1, "video.mp4", str(tmp_path))
    args = mock_run.call_args[0][0]
    assert "-ss" in args
    assert "10.0" in args
    assert "-t" in args
    assert "7.0" in args
    output_filename = Path(output).name
    assert output_filename == "video_Offence_Goal_001.mp4"

def test_export_clip_raises_on_ffmpeg_failure(tmp_path):
    cat = Category(id="cat1", name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(id="c1", category_id="cat1", label="Goal", start=10.0, end=17.0)
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "error message"
    with patch("videotagger.export.ffmpeg_exporter.subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="ffmpeg failed"):
            export_clip(clip, "Offence", 1, "video.mp4", str(tmp_path))

def test_export_playlist_clips_increments_instance(tmp_path):
    cat = Category(id="cat1", name="Offence", color="#e94560", labels=["Goal"])
    c1 = Clip(id="c1", category_id="cat1", label="Goal", start=10.0, end=15.0)
    c2 = Clip(id="c2", category_id="cat1", label="Goal", start=30.0, end=35.0)
    proj = Project(source_video_paths=["video.mp4"], merged_video_path="video.mp4",
                   categories=[cat], clips=[c1, c2])
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("videotagger.export.ffmpeg_exporter.subprocess.run", return_value=mock_result):
        outputs = export_playlist_clips([c1, c2], proj, str(tmp_path))
    assert "Goal_001" in outputs[0]
    assert "Goal_002" in outputs[1]
