"""
Jarvis HUD - Futuristic Iron Man-style overlay

Main HUD window with animated widgets and camera feed.
"""

import sys
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QPainter, QFont
from PyQt5.QtCore import QTimer, Qt
import requests

# Import widgets
from widgets.weather_widget import WeatherWidget
from widgets.voice_widget import VoiceWidget
from graphics.hud_painter import Colors, draw_grid_lines, draw_glow_text, draw_corner_bracket


class JarvisHUD(QWidget):
    """Main Jarvis HUD window."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("JARVIS HUD")
        
        # UI setup
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setScaledContents(True)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # Camera setup
        self.cap = cv2.VideoCapture(
            1 if sys.platform == "win32" else 0,
            cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_AVFOUNDATION
        )
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Get actual dimensions
        ret, frame = self.cap.read()
        if ret:
            self.frame_height, self.frame_width, _ = frame.shape
        else:
            self.frame_width, self.frame_height = 1280, 720
        
        # Initialize widgets
        self.weather_widget = WeatherWidget(50, 150, size=220)
        self.voice_widget = VoiceWidget(
            self.frame_width / 2 - 100,
            self.frame_height / 2 - 100,
            size=200
        )
        
        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)  # ~30 FPS
        
        # Fullscreen
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()
        
        # Fetch initial weather data
        self.fetch_weather()
        
        # Demo: Set voice widget to listening state
        self.voice_widget.set_state("listening")
    
    def fetch_weather(self):
        """Fetch weather data from API."""
        try:
            # Use WeatherAPI.com (same as backend)
            api_key = "2d2eb20b758a451a8bb60232261801"  # From .env
            url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q=Vancouver&aqi=no"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                weather_data = {
                    'location': data['location']['name'],
                    'region': data['location']['region'],
                    'country': data['location']['country'],
                    'temperature': round(data['current']['temp_c']),
                    'feels_like': round(data['current']['feelslike_c']),
                    'condition': data['current']['condition']['text'],
                    'humidity': data['current']['humidity'],
                    'wind_kph': round(data['current']['wind_kph'], 1),
                    'wind_dir': data['current']['wind_dir'],
                    'success': True
                }
                self.weather_widget.update_data(weather_data)
        except Exception as e:
            print(f"Error fetching weather: {e}")
    
    def update_frame(self):
        """Update HUD frame."""
        ret, frame = self.cap.read()
        if not ret:
            return
        
        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qt_image = QImage(frame_rgb.data, w, h, 3 * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        # Create painter
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Draw dark overlay
        painter.fillRect(0, 0, w, h, Colors.DARK)
        
        # Draw animated grid background
        draw_grid_lines(painter, w, h, spacing=80, alpha=20)
        
        # Draw corner brackets
        bracket_size = 30
        draw_corner_bracket(painter, 20, 20, bracket_size, "tl")
        draw_corner_bracket(painter, w - 20, 20, bracket_size, "tr")
        draw_corner_bracket(painter, 20, h - 20, bracket_size, "bl")
        draw_corner_bracket(painter, w - 20, h - 20, bracket_size, "br")
        
        # Draw JARVIS title
        font = QFont("Orbitron", 24, QFont.Bold)
        painter.setFont(font)
        painter.setPen(Colors.PRIMARY)
        painter.drawText(50, 60, "J.A.R.V.I.S.")
        
        # Draw status indicator
        font = QFont("Orbitron", 10)
        painter.setFont(font)
        painter.setPen(Colors.SUCCESS)
        painter.drawText(50, 85, "● ONLINE")
        
        # Draw widgets
        self.weather_widget.draw(painter)
        self.voice_widget.draw(painter)
        
        # Draw footer
        font = QFont("Orbitron", 9)
        painter.setFont(font)
        painter.setPen(Colors.ACCENT)
        painter.drawText(w - 200, h - 30, "JARVIS v1.0 | ACTIVE")
        
        painter.end()
        self.label.setPixmap(pixmap)
    
    def closeEvent(self, event):
        """Clean up on close."""
        self.cap.release()
        super().closeEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key presses."""
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Q:
            self.close()
        elif event.key() == Qt.Key_1:
            # Demo: Toggle voice states
            states = ["idle", "listening", "thinking", "speaking"]
            current_idx = states.index(self.voice_widget.state)
            next_state = states[(current_idx + 1) % len(states)]
            self.voice_widget.set_state(
                next_state,
                "The weather in Vancouver is 3°C with fog." if next_state == "speaking" else ""
            )
        elif event.key() == Qt.Key_2:
            # Demo: Refresh weather
            self.fetch_weather()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set global font
    app.setFont(QFont("Orbitron", 10))
    
    window = JarvisHUD()
    sys.exit(app.exec_())
