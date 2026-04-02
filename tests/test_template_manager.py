import pytest
from videotagger.data.template_manager import TemplateManager
from videotagger.models.project import Category

def test_list_builtin_templates():
    templates = TemplateManager.list_builtin()
    assert "AFL" in templates

def test_load_builtin_afl():
    cats = TemplateManager.load_builtin("AFL")
    names = [c.name for c in cats]
    assert "Offence" in names
    assert "Defence" in names
    labels = next(c.labels for c in cats if c.name == "Offence")
    assert "Goal" in labels

def test_save_and_load_user_template(tmp_path, monkeypatch):
    monkeypatch.setattr("videotagger.data.template_manager.TemplateManager._user_dir",
                        staticmethod(lambda: str(tmp_path)))
    cats = [Category(name="Attack", color="#ff0000", labels=["Shot", "Pass"])]
    TemplateManager.save_user("My Template", cats)
    loaded = TemplateManager.load_user("My Template")
    assert loaded[0].name == "Attack"
    assert "Shot" in loaded[0].labels

def test_list_user_templates(tmp_path, monkeypatch):
    monkeypatch.setattr("videotagger.data.template_manager.TemplateManager._user_dir",
                        staticmethod(lambda: str(tmp_path)))
    cats = [Category(name="X", color="#000", labels=[])]
    TemplateManager.save_user("Custom", cats)
    assert "Custom" in TemplateManager.list_user()
