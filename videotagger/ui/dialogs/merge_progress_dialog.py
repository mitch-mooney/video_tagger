from __future__ import annotations

from typing import List

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox,
    QProgressBar, QPushButton, QVBoxLayout,
)

from videotagger.core.video_merger import VideoMerger


class _MergeThread(QThread):
    progress = pyqtSignal(str)
    succeeded = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, merger: VideoMerger, sources: List[str], output: str):
        super().__init__()
        self._merger = merger
        self._sources = sources
        self._output = output

    def run(self) -> None:
        try:
            self._merger.merge(self._sources, self._output,
                               on_progress=self.progress.emit)
            self.succeeded.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class MergeProgressDialog(QDialog):
    """Modal dialog that runs VideoMerger in a background thread."""

    def __init__(
        self,
        merger: VideoMerger,
        sources: List[str],
        output: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Merging Video Files")
        self.setModal(True)
        self.setMinimumWidth(420)
        self._merger = merger
        self._success = False

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._status_label = QLabel("Starting…")
        layout.addWidget(self._status_label)

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)  # indeterminate
        layout.addWidget(self._bar)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._cancel_btn)
        layout.addLayout(btn_row)

        self._thread = _MergeThread(merger, sources, output)
        self._thread.progress.connect(self._status_label.setText)
        self._thread.succeeded.connect(self._on_success)
        self._thread.failed.connect(self._on_failure)
        self._thread.start()

    def was_successful(self) -> bool:
        return self._success

    def _on_cancel(self) -> None:
        self._merger.cancel()
        self._thread.wait(2000)
        self.reject()

    def _on_success(self) -> None:
        self._success = True
        self.accept()

    def _on_failure(self, message: str) -> None:
        QMessageBox.critical(self, "Merge Failed", message)
        self.reject()
