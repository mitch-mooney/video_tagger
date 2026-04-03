# videotagger/ui/dialogs/tag_manager_dialog.py
from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QInputDialog, QColorDialog, QMessageBox, QLabel,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from videotagger.models.project import Category, Project
from videotagger.data.template_manager import TemplateManager

class TagManagerDialog(QDialog):
    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Tags")
        self.resize(600, 400)
        self._project = project
        self._selected_cat: Category | None = None
        self._setup_ui()
        self._refresh_categories()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        panels = QHBoxLayout()
        outer.addLayout(panels)

        # Categories
        left = QVBoxLayout()
        left.addWidget(QLabel("Categories"))
        self._cat_list = QListWidget()
        self._cat_list.currentItemChanged.connect(self._on_cat_selected)
        left.addWidget(self._cat_list)
        cat_btns = QHBoxLayout()
        for label, slot in [("+ Add", self._add_category), ("Rename", self._rename_category),
                             ("Delete", self._delete_category), ("Color", self._change_color)]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            cat_btns.addWidget(btn)
        left.addLayout(cat_btns)
        panels.addLayout(left)

        # Labels
        right = QVBoxLayout()
        right.addWidget(QLabel("Labels"))
        self._label_list = QListWidget()
        right.addWidget(self._label_list)
        label_btns = QHBoxLayout()
        for lbl, slot in [("+ Add", self._add_label), ("Rename", self._rename_label),
                           ("Delete", self._delete_label)]:
            btn = QPushButton(lbl)
            btn.clicked.connect(slot)
            label_btns.addWidget(btn)
        right.addLayout(label_btns)
        panels.addLayout(right)

        # Bottom
        btm = QHBoxLayout()
        save_tmpl = QPushButton("Save as Template...")
        save_tmpl.clicked.connect(self._save_template)
        load_tmpl = QPushButton("Load Template...")
        load_tmpl.clicked.connect(self._load_template)
        close_btn = QPushButton("Done")
        close_btn.clicked.connect(self.accept)
        btm.addWidget(save_tmpl)
        btm.addWidget(load_tmpl)
        btm.addStretch()
        btm.addWidget(close_btn)
        outer.addLayout(btm)

    def _refresh_categories(self):
        self._cat_list.clear()
        for cat in self._project.categories:
            item = QListWidgetItem(cat.name)
            item.setData(Qt.ItemDataRole.UserRole, cat.id)
            item.setForeground(QColor(cat.color))
            self._cat_list.addItem(item)

    def _refresh_labels(self):
        self._label_list.clear()
        if not self._selected_cat:
            return
        for label in self._selected_cat.labels:
            self._label_list.addItem(label)

    def _on_cat_selected(self, current, previous):
        if not current:
            self._selected_cat = None
            return
        cat_id = current.data(Qt.ItemDataRole.UserRole)
        self._selected_cat = next((c for c in self._project.categories if c.id == cat_id), None)
        self._refresh_labels()

    def _add_category(self):
        name, ok = QInputDialog.getText(self, "Add Category", "Category name:")
        if not ok or not name.strip():
            return
        color = QColorDialog.getColor(QColor("#888888"), self, "Choose color")
        if not color.isValid():
            return
        self._project.categories.append(Category(name=name.strip(), color=color.name()))
        self._refresh_categories()

    def _rename_category(self):
        if not self._selected_cat:
            return
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=self._selected_cat.name)
        if ok and name.strip():
            self._selected_cat.name = name.strip()
            self._refresh_categories()

    def _delete_category(self):
        if not self._selected_cat:
            return
        if QMessageBox.question(self, "Delete", f"Delete '{self._selected_cat.name}'?") \
                == QMessageBox.StandardButton.Yes:
            self._project.categories = [
                c for c in self._project.categories if c.id != self._selected_cat.id
            ]
            self._selected_cat = None
            self._refresh_categories()
            self._refresh_labels()

    def _change_color(self):
        if not self._selected_cat:
            return
        color = QColorDialog.getColor(QColor(self._selected_cat.color), self)
        if color.isValid():
            self._selected_cat.color = color.name()
            self._refresh_categories()

    def _add_label(self):
        if not self._selected_cat:
            return
        name, ok = QInputDialog.getText(self, "Add Label", "Label name:")
        if ok and name.strip():
            self._selected_cat.labels.append(name.strip())
            self._refresh_labels()

    def _rename_label(self):
        item = self._label_list.currentItem()
        if not item or not self._selected_cat:
            return
        old = item.text()
        name, ok = QInputDialog.getText(self, "Rename Label", "New name:", text=old)
        if ok and name.strip():
            idx = self._selected_cat.labels.index(old)
            self._selected_cat.labels[idx] = name.strip()
            self._refresh_labels()

    def _delete_label(self):
        item = self._label_list.currentItem()
        if not item or not self._selected_cat:
            return
        self._selected_cat.labels.remove(item.text())
        self._refresh_labels()

    def _save_template(self):
        name, ok = QInputDialog.getText(self, "Save Template", "Template name:")
        if ok and name.strip():
            TemplateManager.save_user(name.strip(), self._project.categories)
            QMessageBox.information(self, "Saved", f"Template '{name}' saved.")

    def _load_template(self):
        builtin = TemplateManager.list_builtin()
        user = TemplateManager.list_user()
        all_templates = [f"[Built-in] {n}" for n in builtin] + [f"[Custom] {n}" for n in user]
        if not all_templates:
            QMessageBox.information(self, "No Templates", "No templates found.")
            return
        choice, ok = QInputDialog.getItem(
            self, "Load Template", "Choose template:", all_templates, editable=False
        )
        if not ok:
            return
        if self._project.clips:
            reply = QMessageBox.question(
                self, "Load Template",
                "Loading a template replaces current categories. Continue?"
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        if choice.startswith("[Built-in]"):
            cats = TemplateManager.load_builtin(choice.replace("[Built-in] ", ""))
        else:
            cats = TemplateManager.load_user(choice.replace("[Custom] ", ""))
        self._project.categories = cats
        self._selected_cat = None
        self._refresh_categories()
        self._refresh_labels()
