from PyQt5.QtGui import QPainter, QColor, QFont, QPolygonF, QPixmap
from PyQt5.QtCore import Qt, QPointF, QRectF

def draw_glass_panel(painter: QPainter, points, text_lines, icon: QPixmap = None):
    """
    Draws a semi-transparent rounded glass trapezoid with optional icon.
    text_lines: list of strings to draw inside panel.
    icon: QPixmap for sun/cloud icon (optional)
    """
    poly_points = [QPointF(x, y) for x, y in points]
    polygon = QPolygonF(poly_points)

    # Draw semi-transparent panel
    painter.setBrush(QColor(255, 255, 255, 180))
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(polygon)

    # Calculate bounding box
    min_x = min(p.x() for p in poly_points)
    max_x = max(p.x() for p in poly_points)
    min_y = min(p.y() for p in poly_points)
    max_y = max(p.y() for p in poly_points)
    width = max_x - min_x
    height = max_y - min_y
    center_x = min_x + width / 2
    center_y = min_y + height / 2

    # Draw icon if provided
    if icon:
        icon_size = min(width, height) * 0.5
        painter.drawPixmap(
            int(center_x - icon_size / 2),
            int(min_y + 10),
            int(icon_size),
            int(icon_size),
            icon
        )

    # Draw text
    painter.setPen(QColor(0, 0, 0))
    font = QFont("Arial", 10)
    painter.setFont(font)
    metrics = painter.fontMetrics()
    
    total_height = sum(metrics.height() for _ in text_lines)
    start_y = center_y - total_height / 2 + metrics.ascent() + (icon.height() if icon else 0)/2

    for line in text_lines:
        text_width = metrics.horizontalAdvance(line)
        painter.drawText(int(center_x - text_width / 2), int(start_y), line)
        start_y += metrics.height()
