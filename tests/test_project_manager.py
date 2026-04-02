import json, os, pytest
from videotagger.models.project import Category, Clip, Project
from videotagger.data.project_manager import ProjectManager

@pytest.fixture
def sample_project(tmp_path):
    cat = Category(name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(category_id=cat.id, label="Goal", start=10.0, end=15.0)
    return Project(video_path=str(tmp_path / "video.mp4"), categories=[cat], clips=[clip])

def test_save_creates_file(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    assert path.exists()

def test_save_writes_valid_json(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    with open(path) as f:
        data = json.load(f)
    assert data["version"] == 1
    assert data["categories"][0]["name"] == "Offence"

def test_load_round_trip(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    loaded = ProjectManager.load(str(path))
    assert loaded.video_path == sample_project.video_path
    assert loaded.clips[0].start == 10.0

def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        ProjectManager.load("nonexistent.vtp")

def test_load_corrupt_file_raises(tmp_path):
    path = tmp_path / "bad.vtp"
    path.write_text("not json")
    with pytest.raises(ValueError):
        ProjectManager.load(str(path))
