import sys
from PyQt6.QtWidgets import QApplication
from videotagger.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VideoTagger")
    app.setOrganizationName("VideoTagger")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
