import tkinter as tk
from PIL import Image, ImageTk
import cv2
from ultralytics import YOLO
import threading
import time
import os

# ----------------------
# CONFIG
# ----------------------
VIDEO_PATH = "test.mp4"
VEHICLE_CLASSES = [0]  # YOLO vehicle class index
CROP_DIR = "cropped"
HELMET_DIR = "helmet_saved"
os.makedirs(CROP_DIR, exist_ok=True)
os.makedirs(HELMET_DIR, exist_ok=True)

DISPLAY_WIDTH, DISPLAY_HEIGHT = 640, 360  # All streams same size

# ----------------------
# LOAD MODELS
# ----------------------
vehicle_model = YOLO("best.pt").to("cuda:0")
helmet_model = YOLO("best-helmet-2.pt").to("cuda:0")

# ----------------------
# GLOBAL FLAGS & FRAMES
# ----------------------
raw_frame = None
annotated_display_frame = None
cropped_frame = None
helmet_frame = None
first_crop_saved = threading.Event()
last_crop_time = 0
crop_queue = []           # Vehicle crops for helmet processing
helmet_image_queue = []   # Saved helmet images to stream

# ----------------------
# VIDEO CAPTURE
# ----------------------
cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame = cap.read()
if not ret or frame is None:
    raise ValueError(f"Cannot read video file {VIDEO_PATH}")
frame_height, frame_width = frame.shape[:2]

# ----------------------
# FRAME PROCESSING THREAD
# ----------------------
def process_frame():
    global raw_frame, annotated_display_frame, cropped_frame, last_crop_time, crop_queue
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.1)
                continue

        # Vehicle detection
        results = vehicle_model(frame, conf=0.4)
        res = results[0]

        boxes = []
        if res.boxes is not None:
            for box, cls in zip(res.boxes.xyxy, res.boxes.cls):
                if int(cls) in VEHICLE_CLASSES:
                    boxes.append(box)

        annotated_frame = frame.copy()
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0,255,0), 2)

            # Save vehicle crops every 1 second
            current_time = time.time()
            if current_time - last_crop_time >= 1:
                crop = frame[y1:y2, x1:x2]
                if crop is not None and crop.size > 0:
                    filename = os.path.join(CROP_DIR, f"crop_{int(time.time()*1000)}.jpg")
                    cv2.imwrite(filename, crop)
                    last_crop_time = current_time
                    crop_queue.append(crop)
                    if not first_crop_saved.is_set():
                        first_crop_saved.set()

        # Resize frames for Tkinter
        if frame is not None:
            raw_frame = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        if annotated_frame is not None:
            annotated_display_frame = cv2.resize(annotated_frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        if first_crop_saved.is_set() and boxes:
            # Preserve aspect ratio for cropped frame
            box = boxes[0]
            crop = frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
            if crop is not None and crop.size > 0:
                h, w = crop.shape[:2]
                scale = min(DISPLAY_WIDTH / w, DISPLAY_HEIGHT / h)
                new_w, new_h = int(w * scale), int(h * scale)
                cropped_frame = cv2.resize(crop, (new_w, new_h))

        time.sleep(0.03)

# ----------------------
# HELMET DETECTION & SAVE THREAD
# ----------------------
def process_helmet():
    global helmet_image_queue
    while True:
        if not crop_queue:
            time.sleep(0.05)
            continue

        crop_img = crop_queue.pop(0)
        if crop_img is None or crop_img.size == 0:
            continue

        results = helmet_model(crop_img, conf=0.4)
        annotated_crop = results[0].plot()

        # Save every annotated crop regardless of helmet class
        if results[0].boxes is not None and len(results[0].boxes) > 0:
            filename = os.path.join(HELMET_DIR, f"helmet_{int(time.time()*1000)}.jpg")
            cv2.imwrite(filename, annotated_crop)
            helmet_image_queue.append(filename)

        time.sleep(0.05)

# ----------------------
# HELMET STREAM THREAD (SHOW SAVED IMAGES ONE BY ONE)
# ----------------------
def helmet_stream():
    global helmet_frame
    while True:
        if not helmet_image_queue:
            time.sleep(0.05)
            continue

        latest_file = helmet_image_queue.pop(0)
        img = cv2.imread(latest_file)
        if img is not None and img.size > 0:
            h, w = img.shape[:2]
            scale = min(DISPLAY_WIDTH / w, DISPLAY_HEIGHT / h)
            new_w, new_h = int(w * scale), int(h * scale)
            helmet_frame = cv2.resize(img, (new_w, new_h))

        time.sleep(0.05)

# ----------------------
# TKINTER UI (MODERN DARK THEME)
# ----------------------
root = tk.Tk()
root.title("SafeHeads")
root.configure(bg="#1e1e1e")  # Dark background
root.geometry(f"{DISPLAY_WIDTH*2+100}x{DISPLAY_HEIGHT*2+200}")

# Heading style
heading_style = {"font": ("Arial", 14, "bold"), "fg": "#00ff88", "bg": "#1e1e1e"}

# Add headings
tk.Label(root, text="Raw Video", **heading_style).grid(row=0, column=0, pady=10)
tk.Label(root, text="Annotated Video", **heading_style).grid(row=0, column=1, pady=10)
tk.Label(root, text="Cropped Vehicle", **heading_style).grid(row=2, column=0, pady=10)
tk.Label(root, text="Helmet Detection", **heading_style).grid(row=2, column=1, pady=10)

# Frame style for borders
def create_video_frame(parent):
    frame = tk.Frame(parent, bg="#2b2b2b", highlightbackground="#00ff88",
                     highlightthickness=2, bd=0, relief="flat")
    return frame

raw_frame_container = create_video_frame(root)
raw_frame_container.grid(row=1, column=0, padx=20, pady=10)
raw_label = tk.Label(raw_frame_container, bg="#2b2b2b")
raw_label.pack()

annotated_frame_container = create_video_frame(root)
annotated_frame_container.grid(row=1, column=1, padx=20, pady=10)
annotated_label = tk.Label(annotated_frame_container, bg="#2b2b2b")
annotated_label.pack()

cropped_frame_container = create_video_frame(root)
cropped_frame_container.grid(row=3, column=0, padx=20, pady=10)
cropped_label = tk.Label(cropped_frame_container, bg="#2b2b2b")
cropped_label.pack()

helmet_frame_container = create_video_frame(root)
helmet_frame_container.grid(row=3, column=1, padx=20, pady=10)
helmet_label = tk.Label(helmet_frame_container, bg="#2b2b2b")
helmet_label.pack()

def update_frames():
    if raw_frame is not None:
        img = Image.fromarray(cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB))
        raw_label.imgtk = ImageTk.PhotoImage(image=img)
        raw_label.config(image=raw_label.imgtk)

    if annotated_display_frame is not None:
        img = Image.fromarray(cv2.cvtColor(annotated_display_frame, cv2.COLOR_BGR2RGB))
        annotated_label.imgtk = ImageTk.PhotoImage(image=img)
        annotated_label.config(image=annotated_label.imgtk)

    if cropped_frame is not None:
        img = Image.fromarray(cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB))
        cropped_label.imgtk = ImageTk.PhotoImage(image=img)
        cropped_label.config(image=cropped_label.imgtk)

    if helmet_frame is not None:
        img = Image.fromarray(cv2.cvtColor(helmet_frame, cv2.COLOR_BGR2RGB))
        helmet_label.imgtk = ImageTk.PhotoImage(image=img)
        helmet_label.config(image=helmet_label.imgtk)

    root.after(30, update_frames)

# ----------------------
# START THREADS
# ----------------------
threading.Thread(target=process_frame, daemon=True).start()
threading.Thread(target=process_helmet, daemon=True).start()
threading.Thread(target=helmet_stream, daemon=True).start()

# ----------------------
# START TKINTER
# ----------------------
update_frames()
root.mainloop()
