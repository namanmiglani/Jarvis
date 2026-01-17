import cv2
import numpy as np
import datetime

# Windows
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

# MacOs
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

# UI colors (BGR)
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (230, 230, 230)
ACCENT_COLOR = (0, 200, 255)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape

    # ---------- Overlay Layer ----------
    overlay = frame.copy()

    # Top bar
    cv2.rectangle(overlay, (20, 20), (w - 20, 100), BG_COLOR, -1)

    # Blend overlay
    alpha = 0.6
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    # ---------- Text ----------
    now = datetime.datetime.now()
    time_text = now.strftime("%H:%M:%S")
    date_text = now.strftime("%A, %d %B %Y")

    cv2.putText(frame, time_text, (40, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, TEXT_COLOR, 2)

    cv2.putText(frame, date_text, (220, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, TEXT_COLOR, 2)

    # Status indicator
    cv2.circle(frame, (w - 60, 60), 8, ACCENT_COLOR, -1)
    cv2.putText(frame, "LIVE", (w - 120, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, ACCENT_COLOR, 2)

    cv2.imshow("Camera HUD", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

