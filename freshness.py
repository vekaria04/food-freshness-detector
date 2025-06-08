import cv2
import numpy as np
import os

def analyze_freshness(image_path):
    # Load image
    img = cv2.imread(image_path)
    print("DEBUG: image path =", image_path)
    print("DEBUG: img is None?", img is None)
    if img is None:
        raise ValueError(f"Could not read image from path: {image_path}")

    # Convert to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Moldy green range
    lower_green = np.array([75, 80, 40])
    upper_green = np.array([95, 255, 200])

    # Brownish mold range
    lower_brown = np.array([10, 30, 30])
    upper_brown = np.array([25, 255, 200])

    # Combine masks
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)
    mask = cv2.bitwise_or(mask_green, mask_brown)

    # Clean up mask
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    spoil_area = 0
    total_area = img.shape[0] * img.shape[1]
    large_mold_count = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 300:
            spoil_area += area
            large_mold_count += 1
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # Spoilage ratio and scoring
    spoil_ratio = spoil_area / total_area
    print(f"DEBUG: spoil_area = {spoil_area}, total_area = {total_area}, ratio = {spoil_ratio:.5f}")

    if spoil_ratio < 0.0015:
        freshness_score = 100
    else:
        freshness_score = max(0, 100 - (spoil_ratio * 100 * 15.0))  # heavy decay

    # Penalize if there are many mold patches
    if large_mold_count >= 3:
        freshness_score = min(freshness_score, 70)

    # Further cap score if any massive patch found
    for cnt in contours:
        if cv2.contourArea(cnt) > 5000:
            freshness_score = min(freshness_score, 60)

    # Tiered advisory
    if freshness_score > 85:
        advisory = "Fresh - Safe to consume"
    elif freshness_score > 60:
        advisory = "Moderate - Consume soon"
    else:
        advisory = "Spoiled - Do not consume"

    print(f"DEBUG: mold spots = {large_mold_count}, final score = {freshness_score}")

    # Save image
    base, ext = os.path.splitext(image_path)
    result_path = f"{base}_result{ext}"
    cv2.imwrite(result_path, img)

    return freshness_score, advisory, img
