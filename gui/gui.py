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
    QSizePolicy,
)
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QBrush, QPen, QFont

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theremin.theremin import Theremin, POSSIBLE_SCALES, VOLUME_RATIO_BOUNDS, NOTE_NAMES, FrameOverlay


CAMERA_FAILURE_LIMIT = 10


class CaptureWorker(QThread):
    frame_ready = Signal(QImage, object)
    camera_error = Signal(str)

    def __init__(self, theremin: Theremin):
        super().__init__()
        self.theremin = theremin
        self._running = True

    def run(self):
        consecutive_failures = 0
        while self._running:
            success, frame, overlay = self.theremin.capture_frame_and_perform()
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
            self.frame_ready.emit(q_image, overlay)

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
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(1, 1)
        self._current_pixmap = None
        self._current_overlay = None
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

        self.video_label.setMinimumSize(640, 360)
        self.adjustSize()
        self.video_label.setMinimumSize(1, 1)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._display_pixmap()

    def _display_pixmap(self):
        if self._current_pixmap is None:
            return
        scaled = self._current_pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        if self._current_overlay is not None:
            painter = QPainter(scaled)
            painter.setRenderHint(QPainter.Antialiasing)
            self._draw_overlay(painter, scaled.width(), scaled.height(), self._current_overlay)
            painter.end()
        self.video_label.setPixmap(scaled)

    def _draw_overlay(self, painter: QPainter, w: int, h: int, overlay: FrameOverlay):
        dot_r = max(3, w // 100)
        green = QColor(0, 255, 0)
        red = QColor(255, 0, 0)
        blue = QColor(0, 0, 255)

        if overlay.draw_landmarks:
            painter.setPen(Qt.NoPen)
            for hand in overlay.hands:
                for finger in hand.fingers:
                    painter.setBrush(QBrush(red if finger.is_bent else green))
                    px, py = int(finger.tip_x * w), int(finger.tip_y * h)
                    painter.drawEllipse(px - dot_r, py - dot_r, dot_r * 2, dot_r * 2)
                painter.setBrush(QBrush(blue))
                cx, cy = int(hand.control_x * w), int(hand.control_y * h)
                painter.drawEllipse(cx - dot_r, cy - dot_r, dot_r * 2, dot_r * 2)

        if overlay.note is not None:
            note_name = NOTE_NAMES[overlay.note % 12]
            octave = (overlay.note // 12) - 1
            font = QFont()
            font.setPixelSize(max(10, h // 20))
            painter.setFont(font)
            painter.setPen(QPen(green))
            painter.drawText(int(w * 0.04), int(h * 0.08), f"Note: {note_name}{octave}")

        if overlay.volume is not None and overlay.volume_controller_x is not None:
            display_volume = 1.0 - overlay.volume
            ratio_max, ratio_min = VOLUME_RATIO_BOUNDS
            track_top = int(ratio_max * h)
            track_bottom = int((1.0 - ratio_min) * h)
            circle_x = max(6, w // 60)
            circle_y = int(track_bottom - display_volume * (track_bottom - track_top))
            vol_r = max(2, w // 200)

            painter.setPen(QPen(green, 1))
            painter.drawLine(circle_x, track_top, circle_x, track_bottom)

            controller_x = int(overlay.volume_controller_x * w)
            painter.drawLine(controller_x, circle_y, circle_x, circle_y)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(green))
            painter.drawEllipse(circle_x - vol_r, circle_y - vol_r, vol_r * 2, vol_r * 2)

            font = QFont()
            font.setPixelSize(max(8, h // 30))
            painter.setFont(font)
            painter.setPen(QPen(green))
            painter.drawText(circle_x + max(3, w // 120), circle_y - max(2, h // 60),
                             f"{display_volume:.2f}")

    def update_frame(self, q_image: QImage, overlay: FrameOverlay):
        self._current_pixmap = QPixmap.fromImage(q_image)
        self._current_overlay = overlay
        self._display_pixmap()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    theremin = Theremin()
    gui = ThereminGUI(theremin)
    gui.show()
    sys.exit(app.exec())
