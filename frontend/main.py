import cv2
import glass as glass
import time as time
import text as text
import numpy as np

# Windows
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

# MacOs
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)


cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

# Fullscreen Window
cv2.namedWindow("Real-Time Python AR Overlay", cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    "Real-Time Python AR Overlay",
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)

cached_glass = None
frame_count = 0
cache_interval = 3   

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape

    tilted_points = np.float32([
        [400, 50],   # Top Left
        [580, 120],  # Top Right (Pushed down and in)
        [580, 380],  # Bottom Right (Pushed up and in)
        [400, 450]   # Bottom Left
    ])

    # Recompute expensive blur occasionally
    if cached_glass is None or frame_count % cache_interval == 0:
        cached_glass = glass.apply_tilted_glass(frame, tilted_points)

    cv2.imshow("Real-Time Python AR Overlay", cached_glass)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()