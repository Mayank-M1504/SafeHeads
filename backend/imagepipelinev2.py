import os
import cv2
import numpy as np
from PIL import Image

# =============================
# CONFIGURATION
# =============================
# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "violation")      # Folder containing vehicle images
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "enhanced")      # Folder to save enhanced images
MIN_RESOLUTION = 200 * 400   # Minimum width*height allowed (e.g., 400x400)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================
# ENHANCEMENT FUNCTION
# =============================
def enhance_image(image_path):
    """Enhance image contrast, sharpness, and brightness for better number plate visibility."""
    print(f"Processing: {image_path}")

    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"[!] Skipping {image_path}: could not read file.")
        return

    h, w = img.shape[:2]
    if w * h < MIN_RESOLUTION:
        print(f"[!] Skipping {image_path}: below minimum resolution.")
        return

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 1: CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Step 2: Sharpening
    sharpening_kernel = np.array([
        [-1, -1, -1],
        [-1,  9, -1],
        [-1, -1, -1]
    ])
    sharp = cv2.filter2D(enhanced, -1, sharpening_kernel)

    # Step 3: Brightness & Contrast Normalization
    normalized = cv2.normalize(sharp, None, 0, 255, cv2.NORM_MINMAX)

    # Step 4: Slight adaptive thresholding to highlight text
    thresh = cv2.adaptiveThreshold(
        normalized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Step 5: Merge with original for slight blending (retain some natural color)
    final = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    blended = cv2.addWeighted(img, 0.6, final, 0.4, 0)

    # Save result
    filename = os.path.basename(image_path)
    output_path = os.path.join(OUTPUT_DIR, f"enhanced_{filename}")
    cv2.imwrite(output_path, blended)
    print(f"[✓] Enhanced image saved: {output_path}")

# =============================
# MAIN PIPELINE
# =============================
def run_single_image_enhancement():
    print("🚀 Starting single-image enhancement pipeline...\n")
    for file in os.listdir(INPUT_DIR):
        if not file.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        image_path = os.path.join(INPUT_DIR, file)
        enhance_image(image_path)
    print("\n✅ All images enhanced successfully!")

if __name__ == "__main__":
    run_single_image_enhancement()
