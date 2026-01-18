"""
Weather Widget - Futuristic weather display with circular gauge

Displays weather information in an Iron Man-style HUD widget.
"""

from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from graphics.hud_painter import Colors, draw_arc_gauge, draw_hexagon, draw_glow_text
from animations.animator import AnimatedValue, FadeAnimation


class WeatherWidget:
    """Futuristic weather display widget."""
    
    def __init__(self, x, y, size=200):
        """
        Initialize weather widget.
        
        Args:
            x, y: Widget position
            size: Widget size
        """
        self.x = x
        self.y = y
        self.size = size
        self.center_x = x + size / 2
        self.center_y = y + size / 2
        
        # Animated values
        self.temperature = AnimatedValue(0, duration=1.0)
        self.humidity = AnimatedValue(0, duration=1.0)
        self.wind_speed = AnimatedValue(0, duration=1.0)
        self.fade = FadeAnimation(duration=0.5)
        
        # Data
        self.weather_data = None
        self.condition = ""
        
        # Show widget
        self.fade.fade_in()
    
    def update_data(self, weather_data):
        """
        Update weather data.
        
        Args:
            weather_data: Dictionary with weather information
        """
        if not weather_data or not weather_data.get('success'):
            return
        
        self.weather_data = weather_data
        self.temperature.set_target(weather_data['temperature'])
        self.humidity.set_target(weather_data['humidity'])
        self.wind_speed.set_target(weather_data['wind_kph'])
        self.condition = weather_data['condition']
    
    def draw(self, painter: QPainter):
        """Draw the weather widget."""
        if not self.weather_data:
            return
        
        # Update animations
        temp = self.temperature.update()
        humidity = self.humidity.update()
        wind = self.wind_speed.update()
        alpha = self.fade.update()
        
        if alpha < 0.01:
            return
        
        painter.save()
        painter.setOpacity(alpha)
        
        # Draw hexagonal border
        draw_hexagon(painter, self.center_x, self.center_y, self.size / 2 - 10, 
                    color=Colors.PRIMARY, filled=False, glow=True)
        
        # Draw temperature gauge (circular arc)
        gauge_radius = self.size / 2 - 30
        temp_color = self._get_temp_color(temp)
        draw_arc_gauge(painter, self.center_x, self.center_y, gauge_radius,
                      temp + 50, 100, thickness=12, color=temp_color, glow=True)
        
        # Draw temperature text in center
        font = QFont("Orbitron", 32, QFont.Bold)
        painter.setFont(font)
        painter.setPen(Colors.TEXT)
        temp_text = f"{int(temp)}°C"
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(temp_text)
        painter.drawText(
            int(self.center_x - text_width / 2),
            int(self.center_y + 10),
            temp_text
        )
        
        # Draw condition text
        font = QFont("Orbitron", 10)
        painter.setFont(font)
        painter.setPen(Colors.ACCENT)
        metrics = painter.fontMetrics()
        cond_width = metrics.horizontalAdvance(self.condition)
        painter.drawText(
            int(self.center_x - cond_width / 2),
            int(self.center_y + 35),
            self.condition
        )
        
        # Draw humidity and wind indicators
        self._draw_indicators(painter, humidity, wind)
        
        painter.restore()
    
    def _get_temp_color(self, temp):
        """Get color based on temperature."""
        if temp < 0:
            return Colors.SECONDARY  # Blue for cold
        elif temp < 15:
            return Colors.ACCENT  # Light blue for cool
        elif temp < 25:
            return Colors.SUCCESS  # Green for comfortable
        else:
            return Colors.WARNING  # Yellow/orange for hot
    
    def _draw_indicators(self, painter, humidity, wind):
        """Draw humidity and wind indicators."""
        # Humidity indicator (bottom left)
        hum_x = self.center_x - 60
        hum_y = self.center_y + 70
        
        font = QFont("Orbitron", 9)
        painter.setFont(font)
        painter.setPen(Colors.ACCENT)
        painter.drawText(int(hum_x), int(hum_y), f"💧 {int(humidity)}%")
        
        # Wind indicator (bottom right)
        wind_x = self.center_x + 20
        wind_y = self.center_y + 70
        painter.drawText(int(wind_x), int(wind_y), f"💨 {int(wind)} km/h")
