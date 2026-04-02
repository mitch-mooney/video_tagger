import json
from videotagger.models.project import Project, project_to_dict, project_from_dict

class ProjectManager:
    @staticmethod
    def save(project: Project, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(project_to_dict(project), f, indent=2)

    @staticmethod
    def load(path: str) -> Project:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Project file not found: {path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupt project file ({path}): {e}")
        return project_from_dict(data)
