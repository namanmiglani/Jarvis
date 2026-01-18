import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QFont, QPolygonF
from PyQt5.QtCore import QTimer, Qt, QPointF

class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Glass Overlay")
        self.label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Open camera
        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # LEFT trapezoid (tilts inward from left)
        shift_left = 80
        self.left_panel = [
            [100 - shift_left, 100],
            [250 - shift_left, 150],
            [250 - shift_left, 350],
            [100 - shift_left, 400]
        ]

        # RIGHT trapezoid (tilts inward from right)
        shift_right = 80
        self.right_panel = [
            [390 + shift_right, 150],  # Top Left
            [540 + shift_right, 100],  # Top Right
            [540 + shift_right, 400],  # Bottom Right
            [390 + shift_right, 350]   # Bottom Left
        ]

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

        self.label.setAlignment(Qt.AlignCenter)
        self.label.setScaledContents(True)


    def draw_panel(self, painter, points, title):
        poly_points = [QPointF(x, y) for x, y in points]
        polygon = QPolygonF(poly_points)

        # Glass panel
        painter.setBrush(QColor(255, 255, 255, 120))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(polygon)

        # Text setup
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 10))
        metrics = painter.fontMetrics()

        # Bounding box of trapezoid
        min_x = min(p.x() for p in poly_points)
        max_x = max(p.x() for p in poly_points)
        min_y = min(p.y() for p in poly_points)
        max_y = max(p.y() for p in poly_points)

        # Center of shape
        center_x = int((min_x + max_x) / 2)
        center_y = int((min_y + max_y) / 2)

        text_width = metrics.horizontalAdvance(title)
        text_height = metrics.height()

        # Draw text perfectly centered
        painter.drawText(
            int(center_x - text_width / 2),
            int(center_y + text_height / 4),  # optical vertical centering
            title
        )


    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qt_image = QImage(frame_rgb.data, w, h, 3*w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw panels
        self.draw_panel(painter, self.left_panel, "LEFT HUD")
        self.draw_panel(painter, self.right_panel, "RIGHT HUD")

        painter.end()
        self.label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraWindow()
    sys.exit(app.exec_())
