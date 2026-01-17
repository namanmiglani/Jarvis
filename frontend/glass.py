import cv2
import numpy as np
import time

def compute_glass_panel(frame, x, y, w, h):
    sub_face = frame[y:y+h, x:x+w]

    # Downscale → blur → upscale
    small = cv2.resize(sub_face, None, fx=0.5, fy=0.5)
    blur_small = cv2.GaussianBlur(small, (21, 21), 0)
    blur = cv2.resize(blur_small, (w, h))

    overlay = blur.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (255, 255, 255), -1)

    alpha = 0.15
    glass = cv2.addWeighted(overlay, alpha, blur, 1 - alpha, 0)

    return glass

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

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

    # Right-anchored panel
    panel_w = 220
    panel_h = 350
    margin = 40

    px = w - panel_w - margin
    py = int(h * 0.1)

    frame_count += 1

    # Recompute expensive blur occasionally
    if cached_glass is None or frame_count % cache_interval == 0:
        cached_glass = compute_glass_panel(frame, px, py, panel_w, panel_h)

    # Paste cached glass panel
    frame[py:py+panel_h, px:px+panel_w] = cached_glass

    # Panel border
    cv2.rectangle(
        frame,
        (px, py),
        (px + panel_w, py + panel_h),
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    # UI Text
    cv2.putText(frame, "LIVE METRICS",
                (px + 20, py + 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
                cv2.LINE_AA)

    val = int(time.time() % 60)
    cv2.putText(frame, f"Load: {val}%",
                (px + 20, py + 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (255, 255, 255),
                2,
                cv2.LINE_AA)

    cv2.imshow("Real-Time Python AR Overlay", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
