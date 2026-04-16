import json
import os
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

        project = project_from_dict(data)

        # Resolve relative paths against the .vtp file's directory
        vtp_dir = os.path.dirname(os.path.abspath(path))
        if not os.path.isabs(project.merged_video_path):
            project.merged_video_path = os.path.normpath(
                os.path.join(vtp_dir, project.merged_video_path)
            )
        project.source_video_paths = [
            os.path.normpath(os.path.join(vtp_dir, p)) if not os.path.isabs(p) else p
            for p in project.source_video_paths
        ]
        return project
