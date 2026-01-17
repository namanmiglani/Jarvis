import cv2
import numpy as np
import time

def draw_glass_panel(frame, x, y, w, h):
    # 1. Extract and Blur the background region
    sub_face = frame[y:y+h, x:x+w]
    blur = cv2.GaussianBlur(sub_face, (91, 91), 0)
    
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

# Initialize Webcam
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

while True:
    ret, frame = cap.read()
    if not ret: break
    
    # Define Dashboard Position
    px, py, pw, ph = 400, 50, 220, 350
    
    # Draw the Glass
    frame = draw_glass_panel(frame, px, py, pw, ph)
    
    # Add Live Data (Standard OpenCV text)
    cv2.putText(frame, "LIVE METRICS", (px+20, py+40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Simulating a changing number
    val = int(time.time() % 60) 
    cv2.putText(frame, f"Load: {val}%", (px+20, py+100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow("Real-Time Python AR Overlay", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()