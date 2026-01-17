import cv2
import numpy as np
import time

def draw_glass_panel(frame, x, y, w, h):
    # 1. Extract and Blur the background region
    sub_face = frame[y:y+h, x:x+w]
    blur = cv2.GaussianBlur(sub_face, (115, 115), 0)
    
    # 2. Create a semi-transparent white overlay
    overlay = blur.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (255, 255, 255), -1)
    
    # 3. Blend the blur and the white tint (Alpha = 0.15 for transparency)
    alpha = 0.15
    glass_effect = cv2.addWeighted(overlay, alpha, blur, 1 - alpha, 0)
    
    # 4. Put it back into the main frame
    frame[y:y+h, x:x+w] = glass_effect
    
    # 5. Add the "Edge" highlight (1px white border)
    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 1, cv2.LINE_AA)
    
    return frame

