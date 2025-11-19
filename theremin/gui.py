from PySide6.QtWidgets import (
    QMainWindow,
    QApplication,
    QVBoxLayout,
    QLabel,
    QWidget,
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QImage
import cv2
from .theremin import Theremin


class ThereminGUI(QMainWindow):
    def __init__(self, theremin: Theremin):
        super().__init__()
        self.theremin = theremin
        self.setWindowTitle("Theremin")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # video
        self.video_label = QLabel()
        self.layout.addWidget(self.video_label)

        self.theremin.initialize_capture()

        # we need to update frame every 30ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def closeEvent(self, event):
        self.theremin.release_resources()
        event.accept()

    def update_frame(self):
        success, frame = self.theremin.capture_frame_and_perform()
        if success:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame.shape
            bytes_per_line = channel * width
            q_image = QPixmap.fromImage(
                QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            )
            self.video_label.setPixmap(q_image)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    theremin = Theremin()
    gui = ThereminGUI(theremin)
    gui.show()
    sys.exit(app.exec())
