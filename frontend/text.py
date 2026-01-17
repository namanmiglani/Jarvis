import cv2
import numpy as np
import time

def add_text(frame, px, py):
    cv2.putText(frame, "LIVE METRICS", (px+20, py+40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Simulating a changing number
    val = int(time.time() % 60) 
    cv2.putText(frame, f"Load: {val}%", (px+20, py+100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow("Real-Time Python AR Overlay", frame)