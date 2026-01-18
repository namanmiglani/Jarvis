from PyQt5.QtGui import QPainter, QColor, QFont, QPolygonF, QFontMetricsF
from PyQt5.QtCore import Qt, QPointF

def draw_glass_panel(painter, points, text_content):
    """
    Draws a semi-transparent glass trapezoid.
    text_content can be a string (single-line) or list of strings (multi-line)
    """
    poly_points = [QPointF(x, y) for x, y in points]
    polygon = QPolygonF(poly_points)

    # Glass
    painter.setBrush(QColor(255, 255, 255, 120))
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(polygon)

    # Text
    painter.setPen(QColor(0, 0, 0))
    painter.setFont(QFont("Arial", 10))
    metrics = painter.fontMetrics()

    # Bounding box
    min_x = min(p.x() for p in poly_points)
    max_x = max(p.x() for p in poly_points)
    min_y = min(p.y() for p in poly_points)
    max_y = max(p.y() for p in poly_points)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    # Ensure we always have a list of lines
    if isinstance(text_content, str):
        lines = text_content.split("\n")
    else:
        lines = text_content

    total_height = sum(metrics.height() for _ in lines)
    y_offset = center_y - total_height / 2 + metrics.ascent()

    for line in lines:
        text_width = metrics.horizontalAdvance(line)
        painter.drawText(int(center_x - text_width / 2), int(y_offset), line)
        y_offset += metrics.height()
