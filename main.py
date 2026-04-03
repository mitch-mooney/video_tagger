import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from videotagger.ui.main_window import MainWindow

def _check_ffmpeg():
    """Warn on startup if ffmpeg.exe cannot be found."""
    import shutil
    from pathlib import Path
    exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    if (exe_dir / "ffmpeg.exe").exists() or shutil.which("ffmpeg"):
        return
    msg = QMessageBox()
    msg.setWindowTitle("ffmpeg not found")
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setText("ffmpeg.exe was not found next to VideoTagger.exe.")
    msg.setInformativeText(
        "Clip export (.mp4) requires ffmpeg.\n\n"
        "Download it for free:\n"
        "  https://www.gyan.dev/ffmpeg/builds/\n"
        "  → ffmpeg-release-essentials.zip\n\n"
        "Extract ffmpeg.exe and place it in the same\n"
        "folder as VideoTagger.exe.\n\n"
        "You can still tag and review clips without it."
    )
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VideoTagger")
    app.setOrganizationName("VideoTagger")
    _check_ffmpeg()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
