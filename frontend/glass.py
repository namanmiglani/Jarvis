import cv2
import numpy as np
import time

def apply_tilted_glass(frame, tilted_points):
    """
    Apply a blurred, tilted 'glass' effect on the area defined by tilted_points.
    frame: input frame (H x W x 3)
    tilted_points: 4 points of the polygon [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    Returns: frame with glass overlay
    """
    h, w, _ = frame.shape

    # Width/height of the 'flat' virtual rectangle
    rect_w, rect_h = 300, 450

    # Source rectangle (flat)
    pts_src = np.float32([[0,0],[rect_w,0],[rect_w,rect_h],[0,rect_h]])

    # Destination points (tilted polygon)
    pts_dst = np.float32(tilted_points)

    # Perspective transform
    M = cv2.getPerspectiveTransform(pts_src, pts_dst)
    M_inv = cv2.getPerspectiveTransform(pts_dst, pts_src)

    # Warp the tilted area back to flat rectangle
    flat_bg = cv2.warpPerspective(frame, M_inv, (rect_w, rect_h))

    # Apply Gaussian blur to simulate glass
    blur = cv2.GaussianBlur(flat_bg, (91,91), 0)

    # Add semi-transparent overlay to make it look like frosted glass
    overlay = blur.copy()
    cv2.rectangle(overlay, (0,0), (rect_w, rect_h), (255,255,255), -1)
    glass_rect = cv2.addWeighted(overlay, 0.15, blur, 0.85, 0)

    # Add text/UI elements
    cv2.putText(glass_rect, "DASHBOARD", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(glass_rect, f"CPU: {int(time.time()%100)}%", (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255,255,255), 2)

    # Warp glass back onto original frame
    warped_glass = cv2.warpPerspective(glass_rect, M, (w,h))

    # Create mask to blend overlay with original frame
    mask = np.zeros((h,w), dtype=np.uint8)
    cv2.fillConvexPoly(mask, np.int32(pts_dst), 255)
    mask_inv = cv2.bitwise_not(mask)

    bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
    fg = cv2.bitwise_and(warped_glass, warped_glass, mask=mask)

    # Combine background and glass overlay
    result = cv2.add(bg, fg)
    return result
