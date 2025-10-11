import tkinter as tk
from tkinter import Label
from PIL import Image, ImageTk
import cv2
from ultralytics import YOLO
import torch

# --------------------------
# CONFIG
# --------------------------
VIDEO_PATH = "test.mp4"
MODEL_PATH = "best-helmet-2.pt"
TARGET_FPS = 30                 # UI refresh target
CONF_THRESH = 0.25              # adjust as needed
IOU_THRESH  = 0.45
USE_FP16    = True              # set False if you see artifacts on some GPUs

# --------------------------
# DEVICE SETUP (GPU if available)
# --------------------------
if torch.cuda.is_available():
    DEVICE = "cuda:0"
else:
    DEVICE = "cpu"

# Load YOLO model and move to device
model = YOLO(MODEL_PATH)
model.to(DEVICE)

# Try FP16 for speed (only when on CUDA)
if DEVICE.startswith("cuda") and USE_FP16:
    try:
        model.model.half()  # use half precision
    except Exception as e:
        pass

# --------------------------
# VIDEO
# --------------------------
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    raise SystemExit

# --------------------------
# TKINTER UI
# --------------------------
root = tk.Tk()
root.title("YOLO Video Annotator (GPU)")

label_original = Label(root)
label_original.grid(row=0, column=0, padx=10, pady=10)

label_annotated = Label(root)
label_annotated.grid(row=0, column=1, padx=10, pady=10)

# (Optional) simple FPS smoothing
import time
last_time = time.time()
dt_avg = 1.0 / TARGET_FPS

DISPLAY_W, DISPLAY_H = 640, 360   # both original + annotated will be scaled to this size

def update_frame():
    global last_time, dt_avg

    ret, frame = cap.read()
    if not ret:
        cap.release()
        return

    # Run YOLO on GPU with auto-matched image size
    h, w = frame.shape[:2]
    results = model.predict(
        source=frame,
        conf=CONF_THRESH,
        iou=IOU_THRESH,
        verbose=False,
        imgsz=[h, w],   # auto matches video resolution for inference
        half=(DEVICE.startswith("cuda") and USE_FP16),
        device=DEVICE
    )

    # Original frame (resize for display)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb_frame = cv2.resize(rgb_frame, (DISPLAY_W, DISPLAY_H))

    # Annotated frame (resize for display)
    annotated_bgr = results[0].plot()
    annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
    annotated_rgb = cv2.resize(annotated_rgb, (DISPLAY_W, DISPLAY_H))

    # Convert to Tk images
    img_original = ImageTk.PhotoImage(Image.fromarray(rgb_frame))
    img_annotated = ImageTk.PhotoImage(Image.fromarray(annotated_rgb))

    label_original.config(image=img_original)
    label_original.image = img_original
    label_annotated.config(image=img_annotated)
    label_annotated.image = img_annotated

    # Simple fps pacing
    now = time.time()
    dt = now - last_time
    last_time = now
    dt_avg = 0.9 * dt_avg + 0.1 * dt
    delay_ms = max(1, int(1000.0 / max(1e-3, 1.0 / dt_avg)))
    root.after(min(delay_ms, int(1000 / TARGET_FPS)), update_frame)

update_frame()
root.mainloop()
