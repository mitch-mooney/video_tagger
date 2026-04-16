from videotagger.models.project import Category, Clip, Project
from videotagger.export.edl_writer import seconds_to_timecode, write_edl

def test_seconds_to_timecode_simple():
    assert seconds_to_timecode(0.0) == "00:00:00:00"
    assert seconds_to_timecode(1.0) == "00:00:01:00"
    assert seconds_to_timecode(61.0) == "00:01:01:00"
    assert seconds_to_timecode(3661.0) == "01:01:01:00"

def test_seconds_to_timecode_frames():
    # 25fps: 0.04s = 1 frame
    assert seconds_to_timecode(0.04) == "00:00:00:01"
    assert seconds_to_timecode(0.96) == "00:00:00:24"

def test_write_edl_creates_file(tmp_path):
    cat = Category(id="cat1", name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(id="c1", category_id="cat1", label="Goal", start=10.0, end=17.0)
    proj = Project(source_video_paths=["video.mp4"], merged_video_path="video.mp4",
                   categories=[cat], clips=[clip])
    out = str(tmp_path / "out.edl")
    write_edl("Goals", [clip], proj, out)
    content = open(out).read()
    assert "TITLE: Goals" in content
    assert "00:00:10:00" in content   # src_in
    assert "00:00:17:00" in content   # src_out
    assert "Offence - Goal" in content

def test_write_edl_sequential_record_times(tmp_path):
    cat = Category(id="cat1", name="Offence", color="#e94560", labels=["Goal"])
    c1 = Clip(id="c1", category_id="cat1", label="Goal", start=10.0, end=15.0)
    c2 = Clip(id="c2", category_id="cat1", label="Goal", start=30.0, end=38.0)
    proj = Project(source_video_paths=["video.mp4"], merged_video_path="video.mp4",
                   categories=[cat], clips=[c1, c2])
    out = str(tmp_path / "out.edl")
    write_edl("Goals", [c1, c2], proj, out)
    content = open(out).read()
    # c2 record-in should be at 5 seconds (duration of c1)
    assert "00:00:05:00" in content
