from PySide6.QtWidgets import (
    QMainWindow,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QWidget,
)
from PySide6.QtCore import QTimer
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theremin.theremin import Theremin


class ThereminGUI(QMainWindow):
    def __init__(self, theremin: Theremin):
        super().__init__()
        self.theremin = theremin
        self.setWindowTitle("Theremin")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.main_layout.addLayout(self.buttons())

        self.video_label = QLabel()
        self.main_layout.addWidget(self.video_label)

        self.theremin.initialize_capture()

        # we need to update frame every 30ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def buttons(self):
        buttons_layout = QVBoxLayout()

        toggle_landmarks_button = QPushButton("Toggle Landmarks")
        toggle_landmarks_button.clicked.connect(self.toggle_landmarks)
        buttons_layout.addWidget(toggle_landmarks_button)

        cycle_scale_button = QPushButton("Cycle Scale")
        cycle_scale_button.clicked.connect(self.cycle_scale)
        buttons_layout.addWidget(cycle_scale_button)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.close)
        buttons_layout.addWidget(quit_button)

        return buttons_layout

    def toggle_landmarks(self):
        self.theremin.toggle_landmarks()

    def cycle_scale(self):
        self.theremin.cycle_scale()

    def closeEvent(self, event):
        self.theremin.release_resources()
        event.accept()

    def update_frame(self):
        success, q_image = self.theremin.capture_frame_and_perform(use_q_image=True)
        if success:
            self.video_label.setPixmap(q_image)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    theremin = Theremin()
    gui = ThereminGUI(theremin)
    gui.show()
    sys.exit(app.exec())
