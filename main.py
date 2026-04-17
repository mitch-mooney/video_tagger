import os
import sys
from PyQt6.QtWidgets import QApplication
from videotagger.ui.main_window import MainWindow

def main():
    # Qt tries its "ffmpeg" multimedia backend first, but ffmpegmediaplugin.dll
    # ships without its FFmpeg DLL dependencies and fails to load, causing Qt to
    # give up entirely without falling through to the working platform backend.
    # Force the correct platform backend before QApplication is created.
    if sys.platform == 'win32':
        os.environ.setdefault('QT_MEDIA_BACKEND', 'windows')
    elif sys.platform == 'darwin':
        os.environ.setdefault('QT_MEDIA_BACKEND', 'darwin')

    # In a PyInstaller single-file EXE all files are extracted to _MEIPASS.
    # Qt won't find its plugin DLLs there unless we tell it where to look.
    if hasattr(sys, '_MEIPASS'):
        os.environ.setdefault(
            'QT_PLUGIN_PATH',
            os.path.join(sys._MEIPASS, 'PyQt6', 'Qt6', 'plugins'),
        )

    app = QApplication(sys.argv)
    app.setApplicationName("VideoTagger")
    app.setOrganizationName("VideoTagger")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
