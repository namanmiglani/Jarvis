"""
HUD Painter - Core drawing utilities for futuristic Jarvis HUD

Provides reusable drawing functions for creating Iron Man-style interface elements.
"""

import math
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient, QFont, QPainterPath, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QRectF

# Futuristic color palette
class Colors:
    PRIMARY = QColor(0, 255, 255, 200)      # Cyan
    SECONDARY = QColor(0, 150, 255, 200)    # Blue
    ACCENT = QColor(100, 200, 255, 200)     # Light blue
    GLOW = QColor(0, 255, 255, 80)          # Cyan glow
    DARK = QColor(0, 20, 40, 180)           # Dark background
    TEXT = QColor(0, 255, 255, 255)         # Cyan text
    WHITE = QColor(255, 255, 255, 255)      # White
    SUCCESS = QColor(0, 255, 100, 200)      # Green
    WARNING = QColor(255, 200, 0, 200)      # Yellow
    ERROR = QColor(255, 50, 50, 200)        # Red


def draw_arc_gauge(painter: QPainter, center_x: float, center_y: float, radius: float, 
                   value: float, max_value: float, thickness: int = 15, 
                   color: QColor = None, glow: bool = True):
    """
    Draw an animated circular arc gauge (like Iron Man's HUD).
    
    Args:
        painter: QPainter instance
        center_x, center_y: Center coordinates
        radius: Radius of the arc
        value: Current value
        max_value: Maximum value
        thickness: Arc thickness
        color: Arc color (default: PRIMARY)
        glow: Whether to add glow effect
    """
    if color is None:
        color = Colors.PRIMARY
    
    # Calculate arc angle (270 degrees total, starting from bottom)
    start_angle = 135 * 16  # Qt uses 1/16th degree units
    span_angle = int(-270 * 16 * (value / max_value))
    
    # Draw glow effect
    if glow:
        for i in range(3):
            glow_color = QColor(color)
            glow_color.setAlpha(30 - i * 10)
            pen = QPen(glow_color, thickness + i * 4)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawArc(
                int(center_x - radius), int(center_y - radius),
                int(radius * 2), int(radius * 2),
                start_angle, span_angle
            )
    
    # Draw main arc
    pen = QPen(color, thickness)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.drawArc(
        int(center_x - radius), int(center_y - radius),
        int(radius * 2), int(radius * 2),
        start_angle, span_angle
    )


def draw_hexagon(painter: QPainter, center_x: float, center_y: float, size: float, 
                 color: QColor = None, filled: bool = False, glow: bool = True):
    """
    Draw a hexagon with optional glow effect.
    
    Args:
        painter: QPainter instance
        center_x, center_y: Center coordinates
        size: Distance from center to vertex
        color: Hexagon color
        filled: Whether to fill the hexagon
        glow: Whether to add glow effect
    """
    if color is None:
        color = Colors.PRIMARY
    
    # Calculate hexagon points
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = center_x + size * math.cos(angle)
        y = center_y + size * math.sin(angle)
        points.append(QPointF(x, y))
    
    polygon = QPolygonF(points)
    
    # Draw glow
    if glow:
        for i in range(3):
            glow_color = QColor(color)
            glow_color.setAlpha(20 - i * 5)
            pen = QPen(glow_color, 3 + i * 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(polygon)
    
    # Draw main hexagon
    if filled:
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
    else:
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(color, 2))
    
    painter.drawPolygon(polygon)


def draw_glow_text(painter: QPainter, x: float, y: float, text: str, 
                   font_size: int = 12, color: QColor = None, glow: bool = True):
    """
    Draw text with neon glow effect.
    
    Args:
        painter: QPainter instance
        x, y: Text position
        text: Text to draw
        font_size: Font size
        color: Text color
        glow: Whether to add glow effect
    """
    if color is None:
        color = Colors.TEXT
    
    font = QFont("Orbitron", font_size, QFont.Bold)  # Futuristic font
    painter.setFont(font)
    
    # Draw glow
    if glow:
        for i in range(3, 0, -1):
            glow_color = QColor(color)
            glow_color.setAlpha(40 - i * 10)
            painter.setPen(glow_color)
            for dx in range(-i, i + 1):
                for dy in range(-i, i + 1):
                    if dx * dx + dy * dy <= i * i:
                        painter.drawText(int(x + dx), int(y + dy), text)
    
    # Draw main text
    painter.setPen(color)
    painter.drawText(int(x), int(y), text)


def draw_pulse_circle(painter: QPainter, center_x: float, center_y: float, 
                      base_radius: float, pulse_amount: float, 
                      color: QColor = None, glow: bool = True):
    """
    Draw a pulsing circle (for listening indicator).
    
    Args:
        painter: QPainter instance
        center_x, center_y: Center coordinates
        base_radius: Base radius
        pulse_amount: Pulse animation value (0.0 to 1.0)
        color: Circle color
        glow: Whether to add glow effect
    """
    if color is None:
        color = Colors.PRIMARY
    
    radius = base_radius + pulse_amount * 10
    
    # Draw glow
    if glow:
        gradient = QRadialGradient(center_x, center_y, radius + 20)
        glow_color = QColor(color)
        glow_color.setAlpha(int(100 * pulse_amount))
        gradient.setColorAt(0, glow_color)
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            QPointF(center_x, center_y),
            radius + 20, radius + 20
        )
    
    # Draw main circle
    painter.setBrush(Qt.NoBrush)
    pen = QPen(color, 3)
    painter.setPen(pen)
    painter.drawEllipse(
        QPointF(center_x, center_y),
        radius, radius
    )


def draw_grid_lines(painter: QPainter, width: int, height: int, 
                    spacing: int = 50, color: QColor = None, alpha: int = 30):
    """
    Draw animated background grid lines.
    
    Args:
        painter: QPainter instance
        width, height: Canvas dimensions
        spacing: Grid spacing
        color: Line color
        alpha: Line transparency
    """
    if color is None:
        color = Colors.PRIMARY
    
    grid_color = QColor(color)
    grid_color.setAlpha(alpha)
    pen = QPen(grid_color, 1)
    painter.setPen(pen)
    
    # Vertical lines
    for x in range(0, width, spacing):
        painter.drawLine(x, 0, x, height)
    
    # Horizontal lines
    for y in range(0, height, spacing):
        painter.drawLine(0, y, width, y)


def draw_corner_bracket(painter: QPainter, x: float, y: float, size: float, 
                        corner: str = "tl", color: QColor = None, thickness: int = 2):
    """
    Draw corner brackets (like targeting reticles).
    
    Args:
        painter: QPainter instance
        x, y: Corner position
        size: Bracket size
        corner: Corner position ("tl", "tr", "bl", "br")
        color: Bracket color
        thickness: Line thickness
    """
    if color is None:
        color = Colors.PRIMARY
    
    pen = QPen(color, thickness)
    painter.setPen(pen)
    
    if corner == "tl":  # Top-left
        painter.drawLine(int(x), int(y), int(x + size), int(y))
        painter.drawLine(int(x), int(y), int(x), int(y + size))
    elif corner == "tr":  # Top-right
        painter.drawLine(int(x), int(y), int(x - size), int(y))
        painter.drawLine(int(x), int(y), int(x), int(y + size))
    elif corner == "bl":  # Bottom-left
        painter.drawLine(int(x), int(y), int(x + size), int(y))
        painter.drawLine(int(x), int(y), int(x), int(y - size))
    elif corner == "br":  # Bottom-right
        painter.drawLine(int(x), int(y), int(x - size), int(y))
        painter.drawLine(int(x), int(y), int(x), int(y - size))


def draw_rect_frame(painter: QPainter, x: float, y: float, w: float, h: float, 
                    color: QColor = None, thickness: int = 2, filled: bool = True, glow: bool = True):
    """
    Draw a rectangular frame with optional fill and glow.
    """
    if color is None:
        color = Colors.PRIMARY
        
    rect = QRectF(x, y, w, h)
    
    # Draw Fill
    if filled:
        fill_color = QColor(color)
        fill_color.setAlpha(30) # Semi-transparent
        painter.setBrush(QBrush(fill_color))
    else:
        painter.setBrush(Qt.NoBrush)
        
    # Draw Border
    pen = QPen(color, thickness)
    painter.setPen(pen)
    painter.drawRect(rect)
    
    # Draw Glow
    if glow:
        glow_color = QColor(color)
        glow_color.setAlpha(100)
        pen = QPen(glow_color, thickness + 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)
