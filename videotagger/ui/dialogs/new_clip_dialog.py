# videotagger/ui/dialogs/new_clip_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QComboBox, QLineEdit, QDoubleSpinBox, QDialogButtonBox
)
from videotagger.models.project import Clip, Project

class NewClipDialog(QDialog):
    def __init__(self, project: Project, start: float, end: float,
                 preset_category_id=None, preset_label=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Clip")
        self._project = project
        self._clip: Clip | None = None
        layout = QFormLayout(self)

        self._cat_combo = QComboBox()
        for cat in project.categories:
            self._cat_combo.addItem(cat.name, cat.id)
        if preset_category_id:
            idx = self._cat_combo.findData(preset_category_id)
            if idx >= 0:
                self._cat_combo.setCurrentIndex(idx)
        self._cat_combo.currentIndexChanged.connect(self._update_labels)
        layout.addRow("Category:", self._cat_combo)

        self._label_combo = QComboBox()
        self._update_labels()
        if preset_label:
            idx = self._label_combo.findText(preset_label)
            if idx >= 0:
                self._label_combo.setCurrentIndex(idx)
        layout.addRow("Label:", self._label_combo)

        self._start_spin = QDoubleSpinBox()
        self._start_spin.setRange(0, 86400)
        self._start_spin.setDecimals(2)
        self._start_spin.setValue(start)
        layout.addRow("Start (s):", self._start_spin)

        self._end_spin = QDoubleSpinBox()
        self._end_spin.setRange(0, 86400)
        self._end_spin.setDecimals(2)
        self._end_spin.setValue(end)
        layout.addRow("End (s):", self._end_spin)

        self._notes = QLineEdit()
        self._notes.setPlaceholderText("Optional note...")
        layout.addRow("Notes:", self._notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _update_labels(self):
        self._label_combo.clear()
        cat_id = self._cat_combo.currentData()
        cat = next((c for c in self._project.categories if c.id == cat_id), None)
        if cat:
            for label in cat.labels:
                self._label_combo.addItem(label)

    def _accept(self):
        cat_id = self._cat_combo.currentData()
        label = self._label_combo.currentText()
        start = self._start_spin.value()
        end = self._end_spin.value()
        if end <= start:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid", "End time must be after start time.")
            return
        self._clip = Clip(
            category_id=cat_id, label=label,
            start=start, end=end,
            notes=self._notes.text()
        )
        self.accept()

    def clip(self) -> Clip | None:
        return self._clip
