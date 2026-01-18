import sys
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtCore import QTimer, Qt
import requests

import glass


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
        if sys.platform == "win32":
            self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

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

        self.showRightHUD = True
        self.showWeather = True

        self.weatherData = None
        self.fetch_weather()

    def fetch_weather(self):
        url = "https://api.open-meteo.com/v1/forecast?latitude=49.2593&longitude=-123.2475&hourly=temperature_2m,precipitation_probability,wind_speed_10m&forecast_days=1"
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            self.weatherData = {
                "temp": int(data["hourly"]["temperature_2m"][0]),
                "precip": int(data["hourly"]["precipitation_probability"][0]),
                "wind": int(data["hourly"]["wind_speed_10m"][0]),
                "description": "Sunny" if data["hourly"]["temperature_2m"][0] >= 20 else "Cloudy"
            }
            self.showWeather = True
            self.update_frame()  # immediately redraw with weather


    def draw_weather_panel(self, painter, points, weather_data):
        if not weather_data:
            return
        
        content = [
            f"{weather_data['temp']}°C",
            f"{weather_data['precip']}% chance of rain",
            f"{weather_data['wind']} km/h wind",
            weather_data['description']
        ]
        glass.draw_glass_panel(painter, points, content)



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

        if self.showRightHUD:
            glass.draw_glass_panel(painter, self.right_panel, "RIGHT HUD")

        if self.showWeather and self.weatherData:
            self.draw_weather_panel(painter, self.left_panel, self.weatherData)

        painter.end()
        self.label.setPixmap(pixmap)


    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraWindow()
    sys.exit(app.exec_())
