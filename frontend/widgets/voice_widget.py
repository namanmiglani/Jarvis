"""
Voice Widget - Circular voice activity visualization

Displays a pulsing circle when Jarvis is listening/speaking.
"""

from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt
import sys
import os
import math
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from graphics.hud_painter import Colors, draw_pulse_circle, draw_glow_text
from animations.animator import PulseAnimation, FadeAnimation


class VoiceWidget:
    """Voice activity visualization widget."""
    
    def __init__(self, x, y, size=150):
        """
        Initialize voice widget.
        
        Args:
            x, y: Widget position
            size: Widget size
        """
        self.x = x
        self.y = y
        self.size = size
        self.center_x = x + size / 2
        self.center_y = y + size / 2
        
        # Animation
        self.pulse = PulseAnimation(frequency=1.5, amplitude=1.0)
        self.fade = FadeAnimation(duration=0.3)
        
        # State
        self.is_active = False
        self.state = "idle"  # idle, listening, thinking, speaking
        self.response_text = ""
    
    def set_state(self, state, response_text=""):
        """
        Set voice activity state.
        
        Args:
            state: "idle", "listening", "thinking", or "speaking"
            response_text: Response text to display
        """
        self.state = state
        self.response_text = response_text
        
        if state != "idle":
            self.is_active = True
            self.fade.fade_in()
        else:
            self.is_active = False
            self.fade.fade_out()
    
    def draw(self, painter: QPainter):
        """Draw the voice widget."""
        alpha = self.fade.update()
        
        if alpha < 0.01:
            return
        
        painter.save()
        painter.setOpacity(alpha)
        
        # Get pulse value
        pulse = self.pulse.get()
        
        # Draw pulsing circle
        base_radius = self.size / 3
        color = self._get_state_color()
        draw_pulse_circle(painter, self.center_x, self.center_y, 
                         base_radius, pulse, color=color, glow=True)
        
        # Draw inner circle
        inner_radius = base_radius * 0.7
        painter.setBrush(Qt.NoBrush)
        painter.setPen(color)
        painter.drawEllipse(
            int(self.center_x - inner_radius),
            int(self.center_y - inner_radius),
            int(inner_radius * 2),
            int(inner_radius * 2)
        )
        
        # Draw state text
        font = QFont("Orbitron", 10)
        painter.setFont(font)
        painter.setPen(Colors.TEXT)
        metrics = painter.fontMetrics()
        state_text = self.state.upper()
        text_width = metrics.horizontalAdvance(state_text)
        painter.drawText(
            int(self.center_x - text_width / 2),
            int(self.center_y + 5),
            state_text
        )
        
        # Draw response text below if available
        if self.response_text:
            self._draw_response(painter)
        
        painter.restore()
    
    def _get_state_color(self):
        """Get color based on current state."""
        if self.state == "listening":
            return Colors.PRIMARY  # Cyan
        elif self.state == "thinking":
            return Colors.WARNING  # Yellow
        elif self.state == "speaking":
            return Colors.SUCCESS  # Green
        else:
            return Colors.ACCENT  # Light blue
    
    def _draw_response(self, painter):
        """Draw response text below the circle."""
        font = QFont("Orbitron", 12)
        painter.setFont(font)
        painter.setPen(Colors.TEXT)
        
        # Word wrap response text
        max_width = self.size * 2
        words = self.response_text.split()
        lines = []
        current_line = ""
        
        metrics = painter.fontMetrics()
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if metrics.horizontalAdvance(test_line) > max_width:
                if current_line:
                    lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        
        if current_line:
            lines.append(current_line)
        
        # Draw lines
        y_offset = self.center_y + self.size / 2 + 20
        for i, line in enumerate(lines[:3]):  # Max 3 lines
            text_width = metrics.horizontalAdvance(line)
            painter.drawText(
                int(self.center_x - text_width / 2),
                int(y_offset + i * 20),
                line
            )
