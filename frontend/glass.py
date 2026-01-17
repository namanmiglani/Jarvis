import cv2
import numpy as np
import time as time


def apply_tilted_glass(frame, pts_dst):
    fh, fw = frame.shape[:2]
    
    # 1. Define the 'Flat' source dimensions (our virtual workspace)
    # We use the bounding box width/height for a clean workspace
    w, h = 300, 450
    pts_src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    
    # 2. Get the Perspective Matrices
    # M maps from Flat -> Tilted; M_inv maps from Tilted -> Flat
    M = cv2.getPerspectiveTransform(pts_src, pts_dst)
    M_inv = cv2.getPerspectiveTransform(pts_dst, pts_src)
    
    # 3. 'Un-warp' the background pixels from the tilted area into a flat rectangle
    # This allows us to blur the background specifically where the glass is
    flat_bg = cv2.warpPerspective(frame, M_inv, (w, h))
    
    # 4. Apply Glass Effect to the flat rectangle
    blur = cv2.GaussianBlur(flat_bg, (91, 91), 0)
    overlay = blur.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (255, 255, 255), -1)
    glass_rect = cv2.addWeighted(overlay, 0.15, blur, 0.85, 0)
    
    # Add UI elements to the FLAT glass before warping (keeps text crisp)
    cv2.putText(glass_rect, "DASHBOARD", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(glass_rect, f"CPU: {int(time.time()%100)}%", (20, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
    
    # 5. Warp the glass back onto the frame
    warped_glass = cv2.warpPerspective(glass_rect, M, (fw, fh))
    
    # 6. Use a mask to combine the warped glass with the original frame
    mask = np.zeros((fh, fw), dtype=np.uint8)
    cv2.fillConvexPoly(mask, np.int32(pts_dst), 255)
    mask_inv = cv2.bitwise_not(mask)
    
    # Combine everything
    bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
    fg = cv2.bitwise_and(warped_glass, warped_glass, mask=mask)
    
    return cv2.add(bg, fg)
