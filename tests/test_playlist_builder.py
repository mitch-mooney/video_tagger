import pytest
from videotagger.models.project import Category, Clip, Playlist, Project
from videotagger.core.playlist_builder import PlaylistBuilder

@pytest.fixture
def project_with_clips():
    cat = Category(name="Offence", color="#e94560", labels=["Goal"])
    c1 = Clip(category_id=cat.id, label="Goal", start=10.0, end=15.0)
    c2 = Clip(category_id=cat.id, label="Goal", start=30.0, end=35.0)
    return Project(video_path="v.mp4", categories=[cat], clips=[c1, c2]), c1, c2

def test_create_playlist(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    assert pl.name == "Goals"
    assert any(p.id == pl.id for p in proj.playlists)

def test_add_clip_to_playlist(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    builder.add_clip(pl.id, c1.id)
    assert c1.id in pl.clip_ids

def test_add_clip_no_duplicates(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    builder.add_clip(pl.id, c1.id)
    builder.add_clip(pl.id, c1.id)
    assert pl.clip_ids.count(c1.id) == 1

def test_remove_clip(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    builder.add_clip(pl.id, c1.id)
    builder.remove_clip(pl.id, c1.id)
    assert c1.id not in pl.clip_ids

def test_delete_playlist(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    builder.delete_playlist(pl.id)
    assert not any(p.id == pl.id for p in proj.playlists)

def test_get_clips_returns_ordered_clips(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    builder.add_clip(pl.id, c2.id)
    builder.add_clip(pl.id, c1.id)
    clips = builder.get_clips(pl.id)
    assert clips[0].id == c2.id
    assert clips[1].id == c1.id
