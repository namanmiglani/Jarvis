"""
Snapshot Tool - Save and retrieve camera snapshots

Allows users to save camera frames and retrieve them later.
"""

import cv2
import os
import logging
from datetime import datetime
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class SnapshotTool:
    """Tool for saving and retrieving camera snapshots."""
    
    def __init__(self, snapshot_dir="snapshots"):
        """Initialize snapshot tool with storage directory."""
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(exist_ok=True)
        self.camera_manager = None  # Will be set by orchestrator
        logger.info(f"Snapshot Tool initialized (dir: {self.snapshot_dir})")
    
    async def save_snapshot(self) -> Dict:
        """
        Save current camera frame as a snapshot.
        
        Returns:
            Dictionary with success status and snapshot path
        """
        try:
            from agents.camera_manager import CameraManager
            
            # Get camera frame
            if self.camera_manager is None:
                self.camera_manager = CameraManager()
            
            frame = self.camera_manager.get_frame()
            
            if frame is None:
                return {
                    "success": False,
                    "error": "Could not capture camera frame"
                }
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"snapshot_{timestamp}.jpg"
            filepath = self.snapshot_dir / filename
            
            # Save image
            cv2.imwrite(str(filepath), frame)
            
            # Update latest symlink
            latest_path = self.snapshot_dir / "latest.jpg"
            if latest_path.exists():
                latest_path.unlink()
            cv2.imwrite(str(latest_path), frame)
            
            logger.info(f"✅ Snapshot saved: {filename}")
            
            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_latest_snapshot(self) -> Dict:
        """
        Retrieve the most recently saved snapshot.
        
        Returns:
            Dictionary with success status and snapshot info
        """
        try:
            latest_path = self.snapshot_dir / "latest.jpg"
            
            if not latest_path.exists():
                # Try to find the most recent snapshot
                snapshots = sorted(self.snapshot_dir.glob("snapshot_*.jpg"), reverse=True)
                if not snapshots:
                    return {
                        "success": False,
                        "error": "No snapshots found. Please save a snapshot first."
                    }
                latest_path = snapshots[0]
            
            # Read image
            frame = cv2.imread(str(latest_path))
            
            if frame is None:
                return {
                    "success": False,
                    "error": "Could not read snapshot file"
                }
            
            logger.info(f"✅ Retrieved snapshot: {latest_path.name}")
            
            return {
                "success": True,
                "filepath": str(latest_path),
                "filename": latest_path.name,
                "frame": frame
            }
            
        except Exception as e:
            logger.error(f"Error retrieving snapshot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def format_save_response(self, result: Dict) -> str:
        """Format save snapshot result into natural language response."""
        if not result.get('success'):
            return f"I'm sorry, I couldn't save the snapshot. {result.get('error', '')}"
        
        return f"Snapshot saved successfully."
    
    def format_retrieve_response(self, result: Dict) -> str:
        """Format retrieve snapshot result into natural language response."""
        if not result.get('success'):
            return f"I'm sorry, I couldn't retrieve the snapshot. {result.get('error', '')}"
        
        filename = result.get('filename', 'snapshot')
        return f"Here is your most recent snapshot: {filename}. It's displayed on screen."
