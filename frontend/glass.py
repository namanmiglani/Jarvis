from PyQt5.QtGui import QPainter, QColor, QFont, QPolygonF
from PyQt5.QtCore import Qt, QPointF


def draw_glass_panel(painter: QPainter, points, title: str):
    """
    Draws a semi-transparent glass trapezoid with centered text.

    painter : active QPainter
    points  : list of [x, y] defining trapezoid
    title   : text to draw in center
    """

    poly_points = [QPointF(x, y) for x, y in points]
    polygon = QPolygonF(poly_points)

    # Glass panel
    painter.setBrush(QColor(255, 255, 255, 120))
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(polygon)

    # Text setup
    painter.setPen(QColor(0, 0, 0))
    painter.setFont(QFont("Arial", 10))
    metrics = painter.fontMetrics()

    # Bounding box of trapezoid
    min_x = min(p.x() for p in poly_points)
    max_x = max(p.x() for p in poly_points)
    min_y = min(p.y() for p in poly_points)
    max_y = max(p.y() for p in poly_points)

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    text_width = metrics.horizontalAdvance(title)
    text_height = metrics.height()

    # Centered text (optical vertical alignment)
    painter.drawText(
        int(center_x - text_width / 2),
        int(center_y + text_height / 4),
        title
    )
