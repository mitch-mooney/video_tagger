import pytest

from videotagger.core.project_document import ProjectDocument
from videotagger.data.project_manager import ProjectManager
from videotagger.models.project import (
    Category, Clip, Period, Playlist, Project, VideoAngle,
)


def _project(tmp_path):
    return Project(
        source_video_paths=[str(tmp_path / "video.mp4")],
        merged_video_path=str(tmp_path / "video.mp4"),
    )


@pytest.fixture
def doc(tmp_path):
    return ProjectDocument(_project(tmp_path))


class Spy:
    """A subscriber that counts how many times it was notified."""

    def __init__(self):
        self.count = 0

    def __call__(self):
        self.count += 1


def _clip():
    return Clip(category_id="c1", label="Goal", start=1.0, end=2.0)


# ── construction ────────────────────────────────────────────────────────

def test_new_document_is_clean(doc):
    assert doc.is_dirty is False


def test_new_document_exposes_project(tmp_path):
    proj = _project(tmp_path)
    doc = ProjectDocument(proj)
    assert doc.project is proj


def test_path_defaults_to_none(doc):
    assert doc.path is None


# ── clips ───────────────────────────────────────────────────────────────

def test_add_clip_sets_dirty_and_notifies_once(doc):
    spy = Spy()
    doc.subscribe(spy)
    doc.add_clip(_clip())
    assert doc.project.clips and doc.is_dirty is True
    assert spy.count == 1


def test_add_clips_extends_and_notifies_once(doc):
    spy = Spy()
    doc.subscribe(spy)
    doc.add_clips([_clip(), _clip()])
    assert len(doc.project.clips) == 2
    assert spy.count == 1


def test_add_clips_empty_is_noop(doc):
    spy = Spy()
    doc.subscribe(spy)
    doc.add_clips([])
    assert doc.project.clips == []
    assert doc.is_dirty is False
    assert spy.count == 0


def test_remove_last_clip_returns_clip_and_notifies(doc):
    clip = _clip()
    doc.add_clip(clip)
    spy = Spy()
    doc.subscribe(spy)
    removed = doc.remove_last_clip()
    assert removed is clip
    assert doc.project.clips == []
    assert spy.count == 1


def test_remove_last_clip_on_empty_is_noop(doc):
    spy = Spy()
    doc.subscribe(spy)
    assert doc.remove_last_clip() is None
    assert spy.count == 0


# ── angle ───────────────────────────────────────────────────────────────

def test_set_secondary_angle(doc):
    spy = Spy()
    doc.subscribe(spy)
    periods = [Period(name="Q1", primary_start=0.0)]
    angle = VideoAngle(name="Broadcast")
    doc.set_secondary_angle(periods, angle)
    assert doc.project.periods == periods
    assert doc.project.angles == [angle]
    assert doc.is_dirty is True
    assert spy.count == 1


def test_clear_secondary_angle(doc):
    doc.set_secondary_angle([Period(name="Q1", primary_start=0.0)], VideoAngle(name="B"))
    spy = Spy()
    doc.subscribe(spy)
    doc.clear_secondary_angle()
    assert doc.project.angles == []
    assert spy.count == 1


# ── categories ──────────────────────────────────────────────────────────

def test_set_categories(doc):
    spy = Spy()
    doc.subscribe(spy)
    cats = [Category(name="Offence", color="#fff", labels=["Goal"])]
    doc.set_categories(cats)
    assert doc.project.categories == cats
    assert doc.is_dirty is True
    assert spy.count == 1


# ── playlists ───────────────────────────────────────────────────────────

def test_new_playlist_returns_and_notifies(doc):
    spy = Spy()
    doc.subscribe(spy)
    pl = doc.new_playlist("Highlights")
    assert isinstance(pl, Playlist)
    assert pl in doc.project.playlists
    assert spy.count == 1


def test_delete_playlist(doc):
    pl = doc.new_playlist("Highlights")
    spy = Spy()
    doc.subscribe(spy)
    doc.delete_playlist(pl.id)
    assert doc.project.playlists == []
    assert spy.count == 1


def test_add_clip_to_playlist(doc):
    clip = _clip()
    doc.add_clip(clip)
    pl = doc.new_playlist("Highlights")
    spy = Spy()
    doc.subscribe(spy)
    doc.add_clip_to_playlist(pl.id, clip.id)
    assert pl.clip_ids == [clip.id]
    assert spy.count == 1


def test_add_clip_to_playlist_dedupes_without_notify(doc):
    clip = _clip()
    doc.add_clip(clip)
    pl = doc.new_playlist("Highlights")
    doc.add_clip_to_playlist(pl.id, clip.id)
    spy = Spy()
    doc.subscribe(spy)
    doc.add_clip_to_playlist(pl.id, clip.id)  # already present
    assert pl.clip_ids == [clip.id]
    assert spy.count == 0


def test_remove_clip_from_playlist(doc):
    clip = _clip()
    doc.add_clip(clip)
    pl = doc.new_playlist("Highlights")
    doc.add_clip_to_playlist(pl.id, clip.id)
    spy = Spy()
    doc.subscribe(spy)
    doc.remove_clip_from_playlist(pl.id, clip.id)
    assert pl.clip_ids == []
    assert spy.count == 1


def test_reorder_playlist(doc):
    pl = doc.new_playlist("Highlights")
    doc.reorder_playlist(pl.id, ["a", "b", "c"])
    assert pl.clip_ids == ["a", "b", "c"]


def test_clips_of_returns_clips_in_order_filtering_missing(doc):
    c1, c2 = _clip(), _clip()
    doc.add_clips([c1, c2])
    pl = doc.new_playlist("Highlights")
    doc.reorder_playlist(pl.id, [c2.id, "missing", c1.id])
    assert doc.clips_of(pl.id) == [c2, c1]


def test_playlist_op_on_missing_id_raises(doc):
    with pytest.raises(KeyError):
        doc.add_clip_to_playlist("nope", "x")


# ── persistence ─────────────────────────────────────────────────────────

def test_save_requires_path(doc):
    doc.add_clip(_clip())
    with pytest.raises(ValueError):
        doc.save()


def test_save_as_round_trips_and_clears_dirty(tmp_path):
    doc = ProjectDocument(_project(tmp_path))
    doc.add_clip(Clip(category_id="c1", label="Goal", start=10.0, end=15.0))
    assert doc.is_dirty is True

    path = tmp_path / "game.vtp"
    doc.save_as(str(path))

    assert doc.is_dirty is False
    assert doc.path == str(path)
    reloaded = ProjectManager.load(str(path))
    assert reloaded.clips[0].start == 10.0


def test_save_after_save_as_uses_stored_path(tmp_path):
    doc = ProjectDocument(_project(tmp_path))
    path = tmp_path / "game.vtp"
    doc.save_as(str(path))
    doc.add_clip(_clip())
    assert doc.is_dirty is True
    doc.save()  # no path argument — uses stored path
    assert doc.is_dirty is False
    assert len(ProjectManager.load(str(path)).clips) == 1
