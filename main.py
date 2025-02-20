# main.py
import sys
from PySide6.QtWidgets import QApplication
from gui import SaveFileCopier  # gui.py から SaveFileCopier をインポート


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SaveFileCopier()
    window.show()
    sys.exit(app.exec())