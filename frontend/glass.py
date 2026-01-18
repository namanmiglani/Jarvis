from PyQt5.QtGui import QPainter, QColor, QFont, QPolygonF, QPixmap
from PyQt5.QtCore import Qt, QPointF, QRectF
import math


def _panel_bounds(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def draw_weather_panel(painter: QPainter, points, weather):
    """
    Weather panel with:
    - Icon centered inside the panel
    - Text below icon
    - Text tilted less steep relative to bottom edge of panel
    """
    if not weather:
        return

    poly = QPolygonF([QPointF(x, y) for x, y in points])

    # Glass background
    painter.setBrush(QColor(255, 255, 255, 180))
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(poly)

    x0, y0, x1, y1 = _panel_bounds(points)
    width = x1 - x0
    height = y1 - y0

    # --- Offsets ---
    ICON_Y_OFFSET = 15
    TEXT_Y_OFFSET = 10
    TOP_PADDING = 20

    # ----- ICON -----
    icon = weather["icon"]
    max_icon_size = min(width * 0.6, height * 0.4)
    icon = icon.scaled(int(max_icon_size), int(max_icon_size), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    icon_x = x0 + (width - icon.width()) / 2
    icon_y = y0 + TOP_PADDING + ICON_Y_OFFSET
    painter.drawPixmap(int(icon_x), int(icon_y), icon)

    # ----- TEXT -----
    painter.setPen(QColor(0, 0, 0))
    temp_font = QFont("Arial", 14, QFont.Bold)
    desc_font = QFont("Arial", 11)

    # --- Compute reduced tilt based on bottom edge ---
    x1_edge, y1_edge = points[3]  # bottom-left
    x2_edge, y2_edge = points[2]  # bottom-right
    dx = x2_edge - x1_edge
    dy = y2_edge - y1_edge
    full_angle = math.degrees(math.atan2(dy, dx))
    
    REDUCTION_FACTOR = 0.3  # 0.0 = no tilt, 1.0 = full bottom edge tilt
    angle = full_angle * REDUCTION_FACTOR

    # Text starting Y below icon
    text_y = icon_y + icon.height() + 25 + TEXT_Y_OFFSET
    center_x = x0 + width / 2

    # Temperature
    painter.save()
    painter.translate(center_x, text_y)
    painter.rotate(angle)
    painter.setFont(temp_font)
    painter.drawText(QRectF(-width/2, 0, width, 22), Qt.AlignCenter, f"{weather['temp']}°C")
    painter.restore()

    # Description
    painter.save()
    painter.translate(center_x, text_y + 24)
    painter.rotate(angle)
    painter.setFont(desc_font)
    painter.drawText(QRectF(-width/2, 0, width, 20), Qt.AlignCenter, weather["description"])
    painter.restore()

    # Precipitation & wind
    painter.save()
    painter.translate(center_x, text_y + 44)
    painter.rotate(angle)
    painter.setFont(desc_font)
    painter.drawText(QRectF(-width/2, 0, width, 20), Qt.AlignCenter, f"{weather['precip']}% rain · {weather['wind']} km/h")
    painter.restore()




def draw_glass_panel(painter: QPainter, points, text_lines):
    """
    Generic glass panel with text only (no weather dictionary required)
    """
    if not text_lines:
        return

    poly = QPolygonF([QPointF(x, y) for x, y in points])

    # Glass background
    painter.setBrush(QColor(255, 255, 255, 180))
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(poly)

    x0, y0, x1, y1 = _panel_bounds(points)
    width = x1 - x0
    height = y1 - y0

    painter.setPen(QColor(0, 0, 0))
    font = QFont("Arial", 12, QFont.Bold)
    painter.setFont(font)

    metrics = painter.fontMetrics()
    total_height = len(text_lines) * metrics.height()
    start_y = y0 + (height - total_height) / 2 + metrics.ascent()

    for line in text_lines:
        painter.drawText(
            QRectF(x0, start_y - metrics.ascent(), width, metrics.height()),
            Qt.AlignCenter,
            line
        )
        start_y += metrics.height()
