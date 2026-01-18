"""
Camera Manager - Singleton for shared camera access

Provides centralized camera access for both HUD and tools (vision, snapshot, etc.)
"""

import cv2
import threading
import logging

logger = logging.getLogger(__name__)


class CameraManager:
    """Singleton camera manager for shared access."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.cap = None
        self.latest_frame = None
        self._initialized = True
        logger.info("Camera Manager initialized")
    
    def start(self, camera_index=0):
        """Start camera capture."""
        if self.cap is None:
            import sys
            self.cap = cv2.VideoCapture(
                1 if sys.platform == "win32" else camera_index,
                cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_AVFOUNDATION
            )
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            logger.info("Camera started")
    
    def get_frame(self):
        """Get latest camera frame."""
        if self.cap is None:
            self.start()
        
        ret, frame = self.cap.read()
        if ret:
            self.latest_frame = frame
            return frame
        return self.latest_frame
    
    def release(self):
        """Release camera resources."""
        if self.cap:
            self.cap.release()
            logger.info("Camera released")
