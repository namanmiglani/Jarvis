"""
Snapshot Widget - Display saved snapshots with futuristic effects

Shows retrieved snapshots with Iron Man-style animations and borders.
"""

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainter, QImage, QPixmap, QColor
from frontend.graphics.hud_painter import Colors, draw_hexagon, draw_glow_text
from frontend.animations.animator import FadeAnimation, AnimatedValue
import cv2
import numpy as np


class SnapshotWidget:
    """Widget for displaying saved snapshots."""
    
    def __init__(self, x, y, width=400, height=300):
        """
        Initialize snapshot widget.
        
        Args:
            x: X position
            y: Y position
            width: Widget width
            height: Widget height
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # State
        self.snapshot_image = None
        self.snapshot_filename = None
        self.display_time = 0  # Time snapshot has been displayed
        self.auto_fade_duration = 10.0  # Fade out after 10 seconds
        
        # Animations
        self.fade = FadeAnimation(duration=0.5)
        self.border_pulse = AnimatedValue(0, duration=1.0)
        self.fade.fade_out()  # Start hidden
        
        # Border animation state
        self.pulse_direction = 1
    
    def set_snapshot(self, image_data, filename="snapshot.jpg"):
        """
        Set snapshot to display.
        
        Args:
            image_data: numpy array (OpenCV format) or path to image
            filename: Snapshot filename for display
        """
        if isinstance(image_data, str):
            # Load from file path
            self.snapshot_image = cv2.imread(image_data)
        else:
            # Use provided numpy array
            self.snapshot_image = image_data
        
        self.snapshot_filename = filename
        self.display_time = 0  # Reset timer
        self.fade.fade_in()
        
        # Start border pulse animation
        self.border_pulse.set_target(1.0)
    
    def clear_snapshot(self):
        """Clear displayed snapshot."""
        self.snapshot_image = None
        self.snapshot_filename = None
        self.fade.fade_out()
    
    def draw(self, painter: QPainter):
        """Draw the snapshot widget."""
        alpha = self.fade.update()
        
        if alpha <= 0 or self.snapshot_image is None:
            return
        
        # Auto-fade after display duration
        if self.fade.alpha.target == 1.0:  # Only count when fully visible
            self.display_time += 0.016  # Approximate frame time (60 FPS)
            if self.display_time >= self.auto_fade_duration:
                self.fade.fade_out()
        
        painter.setOpacity(alpha)
        
        # Update border pulse
        border_alpha = self.border_pulse.update()
        if border_alpha >= 1.0:
            self.pulse_direction = -1
            self.border_pulse.set_target(0.3)
        elif border_alpha <= 0.3:
            self.pulse_direction = 1
            self.border_pulse.set_target(1.0)
        
        # Draw background panel
        bg_color = QColor(0, 20, 30, 200)  # Dark blue-black
        painter.fillRect(int(self.x), int(self.y), self.width, self.height + 50, bg_color)
        
        # Draw hexagonal corners
        corner_size = 20
        hex_color = Colors.PRIMARY
        hex_color.setAlpha(int(255 * alpha))
        
        # Top-left hexagon
        draw_hexagon(painter, self.x + 10, self.y + 10, corner_size, hex_color)
        # Top-right hexagon
        draw_hexagon(painter, self.x + self.width - 10, self.y + 10, corner_size, hex_color)
        # Bottom-left hexagon
        draw_hexagon(painter, self.x + 10, self.y + self.height + 40, corner_size, hex_color)
        # Bottom-right hexagon
        draw_hexagon(painter, self.x + self.width - 10, self.y + self.height + 40, corner_size, hex_color)
        
        # Draw pulsing border
        border_color = Colors.PRIMARY
        border_color.setAlpha(int(255 * border_alpha * alpha))
        painter.setPen(border_color)
        painter.drawRect(int(self.x), int(self.y), self.width, self.height + 50)
        
        # Draw inner border (cyan glow)
        glow_color = Colors.ACCENT
        glow_color.setAlpha(int(150 * border_alpha * alpha))
        painter.setPen(glow_color)
        painter.drawRect(int(self.x + 2), int(self.y + 2), self.width - 4, self.height + 46)
        
        # Convert and draw snapshot image
        if self.snapshot_image is not None:
            # Convert OpenCV image (BGR) to QImage (RGB)
            h, w = self.snapshot_image.shape[:2]
            
            # Resize to fit widget while maintaining aspect ratio
            aspect_ratio = w / h
            widget_aspect = self.width / self.height
            
            if aspect_ratio > widget_aspect:
                # Image is wider
                new_w = self.width - 20
                new_h = int(new_w / aspect_ratio)
            else:
                # Image is taller
                new_h = self.height - 20
                new_w = int(new_h * aspect_ratio)
            
            resized = cv2.resize(self.snapshot_image, (new_w, new_h))
            rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # Create QImage
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Center image in widget
            img_x = self.x + (self.width - new_w) // 2
            img_y = self.y + 10
            
            painter.drawPixmap(int(img_x), int(img_y), pixmap)
        
        # Draw filename label at bottom
        if self.snapshot_filename:
            label_y = self.y + self.height + 30
            label_x = self.x + self.width // 2
            
            # Center the text manually
            from PyQt5.QtGui import QFont, QFontMetrics
            font = QFont("Orbitron", 12)
            metrics = QFontMetrics(font)
            text_width = metrics.horizontalAdvance(self.snapshot_filename)
            
            draw_glow_text(
                painter,
                label_x - text_width // 2,
                int(label_y),
                self.snapshot_filename,
                font_size=12,
                color=Colors.PRIMARY,
                glow=True
            )
        
        painter.setOpacity(1.0)
