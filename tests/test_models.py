import pytest
from videotagger.models.project import Category, Clip, Playlist, Project
from videotagger.models.project import project_to_dict, project_from_dict


def test_category_has_auto_id():
    cat = Category(name="Offence", color="#e94560", labels=["Goal", "Behind"])
    assert cat.id is not None
    assert len(cat.id) == 36


def test_clip_has_auto_id():
    clip = Clip(category_id="cat-1", label="Goal", start=10.0, end=20.0)
    assert clip.id is not None


def test_project_v2_round_trip():
    cat = Category(name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(category_id=cat.id, label="Goal", start=10.5, end=18.2, notes="Great goal")
    pl = Playlist(name="Best Goals", clip_ids=[clip.id])
    proj = Project(
        source_video_paths=["C:/Q1.mp4", "C:/Q2.mp4"],
        merged_video_path="C:/game_merged.mp4",
        categories=[cat], clips=[clip], playlists=[pl],
    )
    d = project_to_dict(proj)
    proj2 = project_from_dict(d)
    assert proj2.source_video_paths == ["C:/Q1.mp4", "C:/Q2.mp4"]
    assert proj2.merged_video_path == "C:/game_merged.mp4"
    assert proj2.categories[0].name == "Offence"
    assert proj2.clips[0].start == 10.5
    assert proj2.clips[0].notes == "Great goal"
    assert proj2.playlists[0].name == "Best Goals"
    assert proj2.version == 2


def test_project_from_v1_dict_migrates():
    """v1 .vtp files (video_path key) are transparently upgraded to v2."""
    d = {
        "version": 1,
        "video_path": "C:/old_game.mp4",
        "categories": [],
        "clips": [],
        "playlists": [],
    }
    proj = project_from_dict(d)
    assert proj.source_video_paths == ["C:/old_game.mp4"]
    assert proj.merged_video_path == "C:/old_game.mp4"
    assert proj.version == 2


def test_project_from_dict_missing_notes_defaults_empty():
    d = {
        "version": 2,
        "source_video_paths": ["C:/v.mp4"],
        "merged_video_path": "C:/v.mp4",
        "categories": [],
        "clips": [{"id": "c1", "category_id": "cat1", "label": "Goal",
                   "start": 1.0, "end": 2.0}],
        "playlists": [],
    }
    proj = project_from_dict(d)
    assert proj.clips[0].notes == ""
