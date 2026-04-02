# videotagger/ui/tag_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QBrush
from videotagger.models.project import Project

class TagPanel(QWidget):
    label_selected = pyqtSignal(str, str)  # category_id, label

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        layout.addWidget(QLabel("Tags"))
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._tree)

    def refresh(self, project: Project) -> None:
        self._tree.clear()
        for cat in project.categories:
            cat_item = QTreeWidgetItem([cat.name])
            cat_item.setForeground(0, QBrush(QColor(cat.color)))
            cat_item.setData(0, Qt.ItemDataRole.UserRole, ("category", cat.id))
            for label in cat.labels:
                label_item = QTreeWidgetItem([label])
                label_item.setData(0, Qt.ItemDataRole.UserRole, ("label", cat.id, label))
                cat_item.addChild(label_item)
            self._tree.addTopLevelItem(cat_item)
            cat_item.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == "label":
            self.label_selected.emit(data[1], data[2])
