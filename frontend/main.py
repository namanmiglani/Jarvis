import sys
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtCore import QTimer, Qt

import glass  # <-- your new glass module


class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Camera Glass Overlay")

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setScaledContents(True)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Camera
        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # LEFT trapezoid (tilts inward)
        shift_left = 80
        self.left_panel = [
            [100 - shift_left, 100],
            [250 - shift_left, 150],
            [250 - shift_left, 350],
            [100 - shift_left, 400]
        ]

        # RIGHT trapezoid (tilts inward)
        shift_right = 80
        self.right_panel = [
            [390 + shift_right, 150],
            [540 + shift_right, 100],
            [540 + shift_right, 400],
            [390 + shift_right, 350]
        ]

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Fullscreen frameless HUD
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

        self.showHUD = False


    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        qt_image = QImage(
            frame_rgb.data,
            w,
            h,
            3 * w,
            QImage.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qt_image)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw glass panels
        if self.showHUD:
            glass.draw_glass_panel(painter, self.left_panel, "LEFT HUD")
            glass.draw_glass_panel(painter, self.right_panel, "RIGHT HUD")


        painter.end()
        self.label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraWindow()
    sys.exit(app.exec_())
