import cv2
import sys
import os

from PySide6.QtWidgets import (
    QMainWindow,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QWidget,
    QComboBox,
    QMessageBox,
)
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QPixmap, QImage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theremin.theremin import Theremin, POSSIBLE_SCALES


CAMERA_FAILURE_LIMIT = 10


class CaptureWorker(QThread):
    frame_ready = Signal(QImage)
    camera_error = Signal(str)

    def __init__(self, theremin: Theremin):
        super().__init__()
        self.theremin = theremin
        self._running = True

    def run(self):
        consecutive_failures = 0
        while self._running:
            success, frame = self.theremin.capture_frame_and_perform()
            if not success or frame is None:
                consecutive_failures += 1
                if consecutive_failures >= CAMERA_FAILURE_LIMIT:
                    self.camera_error.emit("Camera disconnected or stopped responding.")
                    return
                continue
            consecutive_failures = 0
            h, w, ch = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            q_image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            self.frame_ready.emit(q_image)

    def stop(self):
        self._running = False
        self.wait()


class ThereminGUI(QMainWindow):
    def __init__(self, theremin: Theremin):
        super().__init__()
        self.theremin = theremin
        self.setWindowTitle("Theremin")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.video_label = QLabel()
        self.main_layout.addWidget(self.video_label)

        self.main_layout.addLayout(self.buttons())

        try:
            self.theremin.initialize_capture()
        except RuntimeError as e:
            QMessageBox.critical(self, "Camera Error", str(e))
            raise

        self.worker = CaptureWorker(self.theremin)
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.camera_error.connect(self.on_camera_error)
        self.worker.start()

    def buttons(self):
        buttons_layout = QVBoxLayout()
        buttons_layout.setAlignment(Qt.AlignTop)

        toggle_landmarks_button = QPushButton("Toggle Landmarks")
        toggle_landmarks_button.clicked.connect(self.toggle_landmarks)
        buttons_layout.addWidget(toggle_landmarks_button)

        scale_label = QLabel("Select Scale:")
        buttons_layout.addWidget(scale_label)

        scale_dropdown = QComboBox()
        scale_dropdown.addItems([scale.name for scale in POSSIBLE_SCALES])
        scale_dropdown.currentIndexChanged.connect(self.change_scale)
        buttons_layout.addWidget(scale_dropdown)

        return buttons_layout

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    def toggle_landmarks(self):
        self.theremin.toggle_landmarks()

    def change_scale(self, index):
        self.theremin.scale = POSSIBLE_SCALES[index]

    def showEvent(self, event):
        event.accept()
        QTimer.singleShot(100, self.center_on_screen)

    def closeEvent(self, event):
        self.worker.stop()
        self.theremin.release_resources()
        event.accept()

    def on_camera_error(self, message: str):
        self.worker.stop()
        self.theremin.release_resources()
        QMessageBox.critical(self, "Camera Error", message)
        self.close()

    def update_frame(self, q_image: QImage):
        self.video_label.setPixmap(QPixmap.fromImage(q_image))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    theremin = Theremin()
    gui = ThereminGUI(theremin)
    gui.show()
    sys.exit(app.exec())
