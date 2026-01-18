"""
Jarvis HUD - Futuristic Iron Man-style overlay

Main HUD window with animated widgets, camera feed, and backend integration.
"""

import sys
import cv2
import asyncio
import qasync
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QPainter, QFont
from PyQt5.QtCore import QTimer, Qt

# Import frontend components
from frontend.widgets.weather_widget import WeatherWidget
from frontend.widgets.voice_widget import VoiceWidget
from frontend.graphics.hud_painter import Colors, draw_grid_lines, draw_corner_bracket
from frontend.backend_client import BackendClient
from frontend.animations.animator import AnimatedValue, FadeAnimation


class JarvisHUD(QWidget):
    """Main Jarvis HUD window."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("JARVIZ HUD")
        
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
        
        # HUD state
        self.state = "idle"  # idle, wake_word, listening, thinking, speaking
        self.is_active = False
        
        # Animations
        self.hud_fade = FadeAnimation(duration=0.5)
        self.grid_alpha = AnimatedValue(0, duration=0.5)
        
        # Initialize widgets
        self.weather_widget = WeatherWidget(50, 150, size=220)
        self.weather_widget.fade.fade_out()  # Start hidden
        
        self.voice_widget = VoiceWidget(
            self.frame_width / 2 - 100,
            self.frame_height / 2 - 100,
            size=200
        )
        self.voice_widget.fade.fade_out()  # Start hidden
        
        # Snapshot widget (right side of screen)
        from frontend.widgets.snapshot_widget import SnapshotWidget
        self.snapshot_widget = SnapshotWidget(
            self.frame_width - 450,  # Right side
            150,  # Below top
            width=400,
            height=300
        )
        self.snapshot_widget.fade.fade_out()  # Start hidden
        
        # Backend client
        self.backend_client = BackendClient()
        self.backend_client.on_state_change = self.on_state_change
        self.backend_client.on_weather_update = self.on_weather_update
        self.backend_client.on_snapshot_update = self.on_snapshot_update
        self.backend_client.on_transcription = self.on_transcription
        self.backend_client.on_response = self.on_response
        
        # Connect to backend after event loop starts
        QTimer.singleShot(100, lambda: asyncio.create_task(self.backend_client.connect()))
        
        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)  # ~30 FPS
        
        # Fullscreen
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()
    
    def on_state_change(self, state: str, data: dict):
        """Handle state change from backend."""
        print(f"HUD State: {state}")
        self.state = state
        
        if state == "wake_word":
            # Activate HUD
            self.is_active = True
            self.hud_fade.fade_in()
            self.grid_alpha.set_target(30)
            self.voice_widget.fade.fade_in()
        
        elif state == "idle":
            # Deactivate HUD
            self.is_active = False
            self.hud_fade.fade_out()
            self.grid_alpha.set_target(0)
            self.voice_widget.fade.fade_out()
            self.weather_widget.fade.fade_out()
        
        elif state in ["listening", "thinking", "speaking"]:
            # Update voice widget state
            response_text = data.get("text", "")
            self.voice_widget.set_state(state, response_text)
    
    def on_weather_update(self, weather_data: dict):
        """Handle weather update from backend."""
        print("HUD Weather update received")
        self.weather_widget.update_data(weather_data)
        self.weather_widget.fade.fade_in()
    
    def on_transcription(self, text: str):
        """Handle transcription from backend."""
        print(f"HUD Transcription: {text}")
        # Could display transcription on HUD if desired
    
    def on_response(self, text: str):
        """Handle response from backend."""
        print(f"HUD Response: {text}")
        # Could display response on HUD if desired
    
    def on_snapshot_update(self, snapshot_data: dict):
        """Handle snapshot update from backend."""
        print("HUD Snapshot update received")
        filepath = snapshot_data.get('filepath')
        filename = snapshot_data.get('filename', 'snapshot.jpg')
        
        if filepath:
            self.snapshot_widget.set_snapshot(filepath, filename)
        else:
            print("No snapshot filepath provided")
    
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
        
        # Update animations
        hud_alpha = self.hud_fade.update()
        grid_alpha_val = int(self.grid_alpha.update())
        
        # Draw dark overlay (always visible but subtle when dormant)
        if self.is_active:
            painter.fillRect(0, 0, w, h, Colors.DARK)
        else:
            # Minimal overlay when dormant
            dark_dormant = Colors.DARK
            dark_dormant.setAlpha(50)
            painter.fillRect(0, 0, w, h, dark_dormant)
        
        # Draw animated grid background (only when active)
        if grid_alpha_val > 0:
            draw_grid_lines(painter, w, h, spacing=80, alpha=grid_alpha_val)
        
        # Draw corner brackets (fade in when active)
        if hud_alpha > 0:
            painter.setOpacity(hud_alpha)
            bracket_size = 30
            draw_corner_bracket(painter, 20, 20, bracket_size, "tl")
            draw_corner_bracket(painter, w - 20, 20, bracket_size, "tr")
            draw_corner_bracket(painter, 20, h - 20, bracket_size, "bl")
            draw_corner_bracket(painter, w - 20, h - 20, bracket_size, "br")
            
            # Draw JARVIS title
            font = QFont("Orbitron", 24, QFont.Bold)
            painter.setFont(font)
            painter.setPen(Colors.PRIMARY)
            painter.drawText(50, 60, "J.A.R.V.I.Z.")
            
            # Draw status indicator
            font = QFont("Orbitron", 10)
            painter.setFont(font)
            
            # Status color based on state
            if self.state == "idle":
                status_color = Colors.ACCENT
                status_text = "● STANDBY"
            elif self.state == "listening":
                status_color = Colors.PRIMARY
                status_text = "● LISTENING"
            elif self.state == "thinking":
                status_color = Colors.WARNING
                status_text = "● PROCESSING"
            elif self.state == "speaking":
                status_color = Colors.SUCCESS
                status_text = "● ACTIVE"
            else:
                status_color = Colors.PRIMARY
                status_text = "● ONLINE"
            
            painter.setPen(status_color)
            painter.drawText(50, 85, status_text)
            
            # Draw footer
            font = QFont("Orbitron", 9)
            painter.setFont(font)
            painter.setPen(Colors.ACCENT)
            connection_status = "CONNECTED" if self.backend_client.is_connected() else "DISCONNECTED"
            painter.drawText(w - 250, h - 30, f"JARVIZ v1.0 | {connection_status}")
            
            painter.setOpacity(1.0)
        
        # Draw widgets
        self.weather_widget.draw(painter)
        self.voice_widget.draw(painter)
        self.snapshot_widget.draw(painter)
        
        painter.end()
        self.label.setPixmap(pixmap)
    
    def closeEvent(self, event):
        """Clean up on close."""
        self.cap.release()
        asyncio.create_task(self.backend_client.disconnect())
        """Handle window close event."""
        self.cleanup()
        event.accept()
    
    def cleanup(self):
        """Clean up resources."""
        print("\n🛑 Shutting down HUD...")
        
        # Stop timer
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        # Disconnect backend
        if hasattr(self, 'backend_client') and self.backend_client.is_connected():
            asyncio.create_task(self.backend_client.disconnect())
        
        # Release camera
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        
        print("✅ HUD shutdown complete")
    
    def keyPressEvent(self, event):
        """Handle key presses."""
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Q:
            self.close()


def main():
    """Main entry point."""
    import signal
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set up event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Create HUD
    hud = JarvisHUD()
    hud.show()
    
    # Graceful shutdown on Ctrl+C
    def signal_handler(sig, frame):
        print("\n\n🛑 Received interrupt signal...")
        hud.cleanup()
        loop.stop()
        app.quit()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run event loop
    with loop:
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Keyboard interrupt...")
            hud.cleanup()
        finally:
            loop.close()


if __name__ == "__main__":
    main()
