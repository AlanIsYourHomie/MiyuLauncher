import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


class MiyuLauncher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Miyu Launcher")
        self.resize(1000, 600)

        label = QLabel("Miyu Launcher", self)
        label.setStyleSheet("font-size: 32px;")
        label.adjustSize()
        label.move(40, 40)


def main():
    app = QApplication(sys.argv)

    window = MiyuLauncher()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()