import json, os, pytest
from videotagger.models.project import Category, Clip, Project
from videotagger.data.project_manager import ProjectManager


@pytest.fixture
def sample_project(tmp_path):
    cat = Category(name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(category_id=cat.id, label="Goal", start=10.0, end=15.0)
    return Project(
        source_video_paths=[str(tmp_path / "video.mp4")],
        merged_video_path=str(tmp_path / "video.mp4"),
        categories=[cat],
        clips=[clip],
    )


def test_save_creates_file(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    assert path.exists()


def test_save_writes_version_2(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    with open(path) as f:
        data = json.load(f)
    assert data["version"] == 2
    assert "source_video_paths" in data
    assert "merged_video_path" in data


def test_load_round_trip(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    loaded = ProjectManager.load(str(path))
    assert loaded.source_video_paths == sample_project.source_video_paths
    assert loaded.merged_video_path == sample_project.merged_video_path
    assert loaded.clips[0].start == 10.0


def test_load_v1_file_migrates(tmp_path):
    """A v1 .vtp file (video_path key) loads without error and is migrated."""
    v1_data = {
        "version": 1,
        "video_path": str(tmp_path / "old.mp4"),
        "categories": [],
        "clips": [],
        "playlists": [],
    }
    path = tmp_path / "old.vtp"
    path.write_text(json.dumps(v1_data))
    proj = ProjectManager.load(str(path))
    assert proj.merged_video_path == str(tmp_path / "old.mp4")
    assert proj.source_video_paths == [str(tmp_path / "old.mp4")]


def test_load_packaged_relative_path(tmp_path):
    """A packaged .vtp with merged_video_path='./video.mp4' is resolved relative to the .vtp."""
    pkg_dir = tmp_path / "MyGame"
    pkg_dir.mkdir()
    vtp_data = {
        "version": 2,
        "source_video_paths": ["./video.mp4"],
        "merged_video_path": "./video.mp4",
        "categories": [], "clips": [], "playlists": [],
    }
    vtp_path = pkg_dir / "project.vtp"
    vtp_path.write_text(json.dumps(vtp_data))
    proj = ProjectManager.load(str(vtp_path))
    assert os.path.isabs(proj.merged_video_path)
    assert proj.merged_video_path == str(pkg_dir / "video.mp4")


def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        ProjectManager.load("nonexistent.vtp")


def test_load_corrupt_file_raises(tmp_path):
    path = tmp_path / "bad.vtp"
    path.write_text("not json")
    with pytest.raises(ValueError):
        ProjectManager.load(str(path))
