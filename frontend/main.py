import cv2
import glass as glass
import text as text


# Windows
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

# MacOs
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)


while True:
    ret, frame = cap.read()
    if not ret: break
    
    # Define Dashboard Position
    px, py, pw, ph = 400, 50, 220, 350
    
    # Draw the Box
    frame = glass.draw_glass_panel(frame, px, py, pw, ph)

    frame = text.add_text(frame, px, py)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break