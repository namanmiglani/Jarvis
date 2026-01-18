"""
Maps Widget - Futuristic list for search results
"""

from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTimer
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from graphics.hud_painter import Colors, draw_hexagon, draw_rect_frame
from animations.animator import FadeAnimation

class MapsWidget:
    """Widget to display list of nearby places."""
    
    def __init__(self, x, y, width=400):
        self.x = x
        self.y = y
        self.width = width
        self.places = []
        self.fade = FadeAnimation(duration=1.0)
        
        # Auto-hide timer logic
        self.last_update_time = 0
        self.display_duration = 15.0 # seconds
        self.is_visible = False
        
    def show_results(self, places_list):
        """Update and show results."""
        self.places = places_list[:5] # Show max 5
        self.last_update_time = time.time()
        self.fade.fade_in()
        self.is_visible = True
        
    def draw(self, painter: QPainter):
        """Draw the widget."""
        # Handle auto-fadeout
        if self.is_visible and time.time() - self.last_update_time > self.display_duration:
            self.fade.fade_out()
            if self.fade.get() <= 0.01:
                self.is_visible = False
        
        alpha = self.fade.update()
        if alpha < 0.01:
            return

        painter.save()
        painter.setOpacity(alpha)
        
        # Draw Header
        header_height = 40
        draw_rect_frame(painter, self.x, self.y, self.width, header_height, 
                       color=Colors.PRIMARY, thickness=2)
        
        font = QFont("Orbitron", 14, QFont.Bold)
        painter.setFont(font)
        painter.setPen(Colors.TEXT)
        painter.drawText(int(self.x + 20), int(self.y + 28), "NEARBY PLACES")
        
        # Draw List Items
        item_y = self.y + header_height + 10
        item_height = 70
        
        for i, place in enumerate(self.places):
            # Item Background
            # Determine color based on ranking (Gold for 1st)
            color = Colors.ACCENT
            if i == 0: color = Colors.SUCCESS # Top result green/gold-ish
            
            draw_rect_frame(painter, self.x, item_y, self.width, item_height, 
                           color=color, thickness=1, glow=False)
            
            # Place Name
            font = QFont("Orbitron", 12, QFont.Bold)
            painter.setFont(font)
            painter.setPen(Colors.TEXT)
            painter.drawText(int(self.x + 15), int(item_y + 25), place["name"])
            
            # Rating & Distance
            font = QFont("Orbitron", 10)
            painter.setFont(font)
            
            # Rating (Right aligned)
            rating = place.get("rating", "N/A")
            if rating != "N/A":
                rating_text = f"★ {rating}"
                painter.setPen(Colors.WARNING) # Yellow/Orange
                metrics = painter.fontMetrics()
                w = metrics.horizontalAdvance(rating_text)
                painter.drawText(int(self.x + self.width - w - 15), int(item_y + 25), rating_text)
            
            # Distance (Subtitle)
            painter.setPen(Colors.SECONDARY)
            dist_text = f"{place['distance_km']} km away"
            painter.drawText(int(self.x + 15), int(item_y + 45), dist_text)
            
            # Address (Small)
            font = QFont("Arial", 9) # Arial for potentially complex address chars
            painter.setFont(font)
            painter.setPen(Colors.ACCENT)
            addr = place["address"].split(",")[0] # Just the street part usually
            painter.drawText(int(self.x + 15), int(item_y + 60), addr)
            
            item_y += item_height + 5

        painter.restore()
