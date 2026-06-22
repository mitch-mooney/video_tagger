from videotagger.models.project import (
    Category, Clip, Playlist, Period, VideoAngle, Project,
)

# Pure-model tests only. Serialization, migration, and path resolution are the
# persistence seam's job — see tests/test_project_manager.py.


def test_category_has_auto_id():
    cat = Category(name="Offence", color="#e94560", labels=["Goal", "Behind"])
    assert cat.id is not None
    assert len(cat.id) == 36


def test_clip_has_auto_id():
    clip = Clip(category_id="cat-1", label="Goal", start=10.0, end=20.0)
    assert clip.id is not None


def test_project_defaults_to_current_version():
    proj = Project(source_video_paths=["v.mp4"], merged_video_path="v.mp4")
    assert proj.version == 3
    assert proj.clips == []
    assert proj.periods == []
    assert proj.angles == []


def test_distinct_entities_get_distinct_ids():
    a = Clip(category_id="c", label="x", start=0.0, end=1.0)
    b = Clip(category_id="c", label="x", start=0.0, end=1.0)
    assert a.id != b.id
