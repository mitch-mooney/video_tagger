# videotagger/ui/dialogs/new_project_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDialogButtonBox, QFileDialog, QMessageBox
)
from videotagger.models.project import Project
from videotagger.data.template_manager import TemplateManager

class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(480)
        self._project: Project | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select video file:"))
        file_row = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Path to .mp4 / .mov ...")
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse)
        file_row.addWidget(self._path_edit, stretch=1)
        file_row.addWidget(browse)
        layout.addLayout(file_row)

        layout.addWidget(QLabel("Start from template (optional):"))
        self._tmpl_combo = QComboBox()
        self._tmpl_combo.addItem("— None (blank) —", None)
        for name in TemplateManager.list_builtin():
            self._tmpl_combo.addItem(f"[Built-in] {name}", ("builtin", name))
        for name in TemplateManager.list_user():
            self._tmpl_combo.addItem(f"[Custom] {name}", ("user", name))
        layout.addWidget(self._tmpl_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "",
            "Video Files (*.mp4 *.mov *.avi *.mkv *.m4v);;All Files (*)"
        )
        if path:
            self._path_edit.setText(path)

    def _accept(self):
        path = self._path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "Required", "Please select a video file.")
            return
        tmpl_data = self._tmpl_combo.currentData()
        categories = []
        if tmpl_data:
            kind, name = tmpl_data
            if kind == "builtin":
                categories = TemplateManager.load_builtin(name)
            else:
                categories = TemplateManager.load_user(name)
        self._project = Project(video_path=path, categories=categories)
        self.accept()

    def project(self) -> Project | None:
        return self._project
