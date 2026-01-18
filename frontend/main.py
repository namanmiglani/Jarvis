import sys
import cv2
import requests
import glass
import os

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtCore import QTimer, Qt


class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Glass Overlay")

        self.label = QLabel(alignment=Qt.AlignCenter)
        self.label.setScaledContents(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        # Camera
        self.cap = cv2.VideoCapture(
            1 if sys.platform == "win32" else 0,
            cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_AVFOUNDATION
        )
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Panels
        self.left_panel = [[20, 100], [170, 150], [170, 350], [20, 400]]
        self.right_panel = [[470, 150], [620, 100], [620, 400], [470, 350]]

        # Assets (ABSOLUTE PATH – IMPORTANT)
        base = os.path.dirname(os.path.abspath(__file__))
        self.sun_icon = QPixmap(os.path.join(base, "assests", "sun.png"))
        self.cloud_icon = QPixmap(os.path.join(base, "assests", "cloud.png"))

        self.weatherData = None
        self.showWeather = True
        self.showRightHUD = True

        self.fetch_weather()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

    def fetch_weather(self):
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=49.2593&longitude=-123.2475"
            "&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
            "&forecast_days=1"
        )

        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return

        data = r.json()
        temp = int(data["hourly"]["temperature_2m"][0])

        self.weatherData = {
            "temp": temp,
            "precip": int(data["hourly"]["precipitation_probability"][0]),
            "wind": int(data["hourly"]["wind_speed_10m"][0]),
            "description": "Sunny" if temp >= 20 else "Cloudy",
            "icon": self.sun_icon if temp >= 20 else self.cloud_icon
        }

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape

        pixmap = QPixmap.fromImage(
            QImage(frame.data, w, h, 3 * w, QImage.Format_RGB888)
        )

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.showRightHUD:
            glass.draw_glass_panel(painter, self.right_panel, ["RIGHT HUD"])

        if self.showWeather:
            glass.draw_weather_panel(painter, self.left_panel, self.weatherData)


        painter.end()
        self.label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraWindow()
    sys.exit(app.exec_())
