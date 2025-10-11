from flask import Flask, Response, request, jsonify, render_template_string, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import cv2
import numpy as np
from ultralytics import YOLO
import json
import threading
import time
from datetime import datetime
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import os
import json
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# No file size limit - removed MAX_CONTENT_LENGTH setting



# -----------------------------
# Simple IOU-based object tracker
# -----------------------------
def _compute_iou(box_a, box_b):
    """Compute IOU between two boxes [x1,y1,x2,y2]."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    denom = area_a + area_b - inter_area
    if denom <= 0:
        return 0.0
    return inter_area / denom

class SimpleTracker:
    """Greedy IOU-based tracker assigning persistent IDs to detections across frames."""
    def __init__(self, iou_threshold=0.3, max_idle_seconds=2.0):
        self.iou_threshold = iou_threshold
        self.max_idle_seconds = max_idle_seconds
        self.next_id = 1
        # id -> { 'bbox': [...], 'last_seen': timestamp }
        self.tracks = {}

    def _cleanup(self, now_ts):
        # Remove tracks not seen recently
        to_delete = []
        for track_id, track in self.tracks.items():
            if now_ts - track['last_seen'] > self.max_idle_seconds:
                to_delete.append(track_id)
        for tid in to_delete:
            del self.tracks[tid]

    def update(self, detections):
        """
        detections: list of { 'bbox': [x1,y1,x2,y2], ... }
        Returns detections with 'track_id' assigned.
        """
        now_ts = time.time()
        self._cleanup(now_ts)

        # Prepare matching
        unmatched_track_ids = set(self.tracks.keys())
        assigned_tracks = {}

        # Greedy assignment by IOU: for each detection, find best track above threshold
        for det_idx, det in enumerate(detections):
            best_tid = None
            best_iou = 0.0
            for tid in list(unmatched_track_ids):
                iou = _compute_iou(det['bbox'], self.tracks[tid]['bbox'])
                if iou > self.iou_threshold and iou > best_iou:
                    best_iou = iou
                    best_tid = tid
            if best_tid is not None:
                assigned_tracks[det_idx] = best_tid
                unmatched_track_ids.discard(best_tid)

        # Assign existing IDs and update their state
        for det_idx, tid in assigned_tracks.items():
            det = detections[det_idx]
            det['track_id'] = tid
            self.tracks[tid]['bbox'] = det['bbox']
            self.tracks[tid]['last_seen'] = now_ts

        # Create new IDs for unassigned detections
        for det_idx, det in enumerate(detections):
            if det_idx in assigned_tracks:
                continue
            tid = self.next_id
            self.next_id += 1
            det['track_id'] = tid
            self.tracks[tid] = {
                'bbox': det['bbox'],
                'last_seen': now_ts
            }

        return detections

def load_yolo_model_safe(model_path):
    """
    Safely load YOLO model with PyTorch 2.6 compatibility.
    Handles the weights_only parameter issue.
    """
    try:
        # Method 1: Try with safe globals
        import torch
        from ultralytics.nn.tasks import DetectionModel
        
        # Add safe globals for YOLO model loading
        torch.serialization.add_safe_globals([DetectionModel])
        
        model = YOLO(model_path)
        return model
        
    except Exception as e1:
        try:
            # Method 2: Monkey patch torch.load
            import torch
            original_load = torch.load
            
            def safe_load(*args, **kwargs):
                kwargs['weights_only'] = False
                return original_load(*args, **kwargs)
            
            torch.load = safe_load
            model = YOLO(model_path)
            torch.load = original_load  # Restore original
            
            return model
            
        except Exception as e2:
            try:
                # Method 3: Set environment variable
                import os
                os.environ['TORCH_SERIALIZATION_WEIGHTS_ONLY'] = 'False'
                model = YOLO(model_path)
                return model
                
            except Exception as e3:
                raise Exception(f"Could not load YOLO model {model_path}. Try updating ultralytics or downgrading PyTorch.")

class VideoInferenceProcessor:
    def __init__(self, vehicle_model_path="best.pt", helmet_model_path="helmetv3.pt"):
        """Initialize the video inference processor with local YOLO models."""
        # Detect and set up GPU/CPU device
        self.device = self.detect_device()
        
        # Load models using safe loading function
        self.vehicle_model = load_yolo_model_safe(vehicle_model_path)
        self.helmet_model = load_yolo_model_safe(helmet_model_path)
        
        # Move models to device
        self.setup_models_on_device()
        
        self.camera = None
        self.video_source = None  # Can be camera index or video file path
        self.source_type = "camera"  # "camera" or "video"
        self.is_streaming = False
        self.detection_mode = "vehicle"  # "vehicle", "helmet", or "both"
        self.detection_enabled = True
        self.confidence_threshold = 0.3
        self.vehicle_classes = [0]  # YOLO vehicle class indices
        
        # Video playback controls
        self.is_paused = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        
        # Create directories for saving crops
        self.crop_dir = "cropped"
        self.helmet_dir = "helmet_saved"
        self.cropped_images_dir = "cropped_images"  # New directory for vehicle crops
        self.helmet_results_dir = "helmet_results"  # Directory for helmet detection results
        self.violation_dir = "violation"  # Directory for no helmet violations
        os.makedirs(self.crop_dir, exist_ok=True)
        os.makedirs(self.helmet_dir, exist_ok=True)
        os.makedirs(self.cropped_images_dir, exist_ok=True)
        os.makedirs(self.helmet_results_dir, exist_ok=True)
        os.makedirs(self.violation_dir, exist_ok=True)
        
        # Auto-save timing
        self.last_save_time = 0
        self.save_interval = 1.0  # Save every 1 second
        
        # Minimum crop size requirements
        self.min_crop_width = 290
        self.min_crop_height = 450
        
        # Analysis results (now handled by separate pipeline)
        self.analysis_results = {}  # Store analysis results by filename
        
        # Tracking: assign persistent IDs to vehicles
        self.tracker = SimpleTracker(iou_threshold=0.35, max_idle_seconds=2.5)

        # Region of Interest (ROI) polygon for filtering detections
        # Stored as list of [x, y] points in image coordinates
        self.roi_enabled = False
        self.roi_polygon = []
        
        # Helmet detection pipeline
        self.helmet_detection_enabled = True
        self.helmet_results = []  # Store helmet detection results
        self.last_helmet_analysis_time = 0
        self.helmet_analysis_interval = 0.5  # Analyze crops every 0.5 seconds
        self.violations = []  # Store violation records
        
        # Number plate extraction (placeholder - you can implement OCR here)
        self.number_plate_counter = 1
    
    def detect_device(self):
        """Detect the best available device (GPU/CPU)."""
        try:
            import torch
            
            # Check if CUDA is available
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                # Use the first GPU
                device = "cuda:0"
                
                # Test GPU availability
                try:
                    test_tensor = torch.tensor([1.0]).to(device)
                    return device
                except Exception as e:
                    return "cpu"
            else:
                return "cpu"
                
        except ImportError:
            return "cpu"
        except Exception as e:
            return "cpu"
    
    def setup_models_on_device(self):
        """Move models to the detected device."""
        try:
            if self.device != "cpu":
                # Move vehicle model
                self.vehicle_model.to(self.device)
                
                # Move helmet model  
                self.helmet_model.to(self.device)
                
                # Optimize GPU backends
                import torch
                if torch.backends.cudnn.is_available():
                    torch.backends.cudnn.benchmark = True
                try:
                    if hasattr(torch.backends.cuda, 'matmul'):
                        torch.backends.cuda.matmul.allow_tf32 = True
                except Exception:
                    pass
                
        except Exception as e:
            self.device = "cpu"
            
            # Ensure models are on CPU
            try:
                self.vehicle_model.to("cpu")
                self.helmet_model.to("cpu")
            except:
                pass
        
    def start_source(self, source, source_type="camera"):
        """Start video capture from camera or video file."""
        try:
            self.video_source = source
            self.source_type = source_type
            
            if source_type == "camera":
                self.camera = cv2.VideoCapture(int(source))
                if not self.camera.isOpened():
                    # Try with different backends
                    self.camera = cv2.VideoCapture(int(source), cv2.CAP_DSHOW)
                
                if self.camera.isOpened():
                    # Set camera properties for better performance
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.camera.set(cv2.CAP_PROP_FPS, 30)
                    self.fps = 30
                    self.total_frames = 0  # Live camera has no total frames
                    return True
                    
            elif source_type == "video":
                if not os.path.exists(source):
                    return False
                
                self.camera = cv2.VideoCapture(source)
                if self.camera.isOpened():
                    # Get video properties
                    self.fps = self.camera.get(cv2.CAP_PROP_FPS)
                    self.total_frames = int(self.camera.get(cv2.CAP_PROP_FRAME_COUNT))
                    self.current_frame = 0
                    return True
            
            return False
            
        except Exception as e:
            return False
    
    def start_camera(self, camera_index=0):
        """Legacy method - start camera capture."""
        return self.start_source(camera_index, "camera")
    
    def stop_camera(self):
        """Stop the camera capture."""
        if self.camera:
            self.camera.release()
            self.camera = None
        self.is_streaming = False
        self.is_paused = False
    
    def pause_video(self):
        """Pause video playback (only works for video files)."""
        if self.source_type == "video":
            self.is_paused = True
            return True
        return False
    
    def resume_video(self):
        """Resume video playback."""
        if self.source_type == "video":
            self.is_paused = False
            return True
        return False
    
    def seek_video(self, frame_number):
        """Seek to specific frame in video."""
        if self.source_type == "video" and self.camera:
            try:
                frame_number = max(0, min(frame_number, self.total_frames - 1))
                self.camera.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                self.current_frame = frame_number
                return True
            except Exception as e:
                pass
        return False
    
    def get_video_info(self):
        """Get current video information."""
        if self.camera and self.camera.isOpened():
            return {
                'source_type': self.source_type,
                'source': self.video_source,
                'current_frame': self.current_frame,
                'total_frames': self.total_frames,
                'fps': self.fps,
                'is_paused': self.is_paused,
                'duration_seconds': self.total_frames / self.fps if self.fps > 0 else 0
            }
        return None
    
    def get_device_info(self):
        """Get current device information."""
        try:
            import torch
            
            info = {
                'device': self.device,
                'cuda_available': torch.cuda.is_available(),
                'device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0
            }
            
            if torch.cuda.is_available() and self.device != "cpu":
                gpu_index = int(self.device.split(':')[1]) if ':' in self.device else 0
                info.update({
                    'gpu_name': torch.cuda.get_device_name(gpu_index),
                    'gpu_memory_total': torch.cuda.get_device_properties(gpu_index).total_memory / 1024**3,
                    'gpu_memory_allocated': torch.cuda.memory_allocated(gpu_index) / 1024**3,
                    'gpu_memory_cached': torch.cuda.memory_reserved(gpu_index) / 1024**3
                })
            
            return info
            
        except Exception as e:
            return {
                'device': self.device,
                'error': str(e)
            }
    
    
    def save_vehicle_crops(self, frame, vehicle_detections):
        """Save cropped vehicle images every 2 seconds (only if larger than 135x332)."""
        current_time = time.time()
        
        # Check if enough time has passed since last save
        if current_time - self.last_save_time < self.save_interval:
            return
        
        # Only save if we have vehicle detections
        if not vehicle_detections:
            return
        
        try:
            timestamp = int(current_time * 1000)  # Millisecond timestamp
            saved_count = 0
            skipped_count = 0
            
            for i, detection in enumerate(vehicle_detections):
                x1, y1, x2, y2 = detection['bbox']
                
                # Ensure coordinates are valid
                if x2 <= x1 or y2 <= y1:
                    continue
                
                # Calculate crop dimensions
                crop_width = x2 - x1
                crop_height = y2 - y1
                
                # Check minimum size requirements
                if crop_width < self.min_crop_width or crop_height < self.min_crop_height:
                    skipped_count += 1
                    continue
                
                # Crop the vehicle region
                cropped_vehicle = frame[y1:y2, x1:x2]
                
                if cropped_vehicle.size == 0:
                    continue
                
                # Create filename with timestamp, vehicle ID, and detection info
                confidence = detection.get('confidence', 0)
                track_id = detection.get('track_id', 'unknown')
                filename = f"vehicle_{timestamp}_ID{track_id}_{crop_width}x{crop_height}_conf{confidence:.2f}.jpg"
                filepath = os.path.join(self.cropped_images_dir, filename)
                
                # Save the cropped image
                success = cv2.imwrite(filepath, cropped_vehicle)
                if success:
                    saved_count += 1
            
            if saved_count > 0 or skipped_count > 0:
                self.last_save_time = current_time
                
        except Exception as e:
            pass
    
    # Note: Gemini analysis functions removed - now handled by separate pipeline
    
    def process_helmet_detection_on_crops(self):
        """Process helmet detection on recently saved vehicle crops."""
        if not self.helmet_detection_enabled:
            return
        
        current_time = time.time()
        
        # Check if enough time has passed since last helmet analysis
        if current_time - self.last_helmet_analysis_time < self.helmet_analysis_interval:
            return
        
        try:
            # Get list of recent crop files
            if not os.path.exists(self.cropped_images_dir):
                return
            
            crop_files = [f for f in os.listdir(self.cropped_images_dir) if f.endswith('.jpg')]
            if not crop_files:
                return
            
            # Sort by modification time and get the most recent ones
            crop_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.cropped_images_dir, x)), reverse=True)
            
            # Process the 5 most recent crops
            recent_crops = crop_files[:5]
            
            for crop_file in recent_crops:
                crop_path = os.path.join(self.cropped_images_dir, crop_file)
                
                # Check if we've already processed this file recently
                result_file = os.path.join(self.helmet_results_dir, f"helmet_{crop_file}")
                if os.path.exists(result_file):
                    # Skip if result file is newer than crop file
                    if os.path.getmtime(result_file) > os.path.getmtime(crop_path):
                        continue
                
                # Load the crop image
                crop_image = cv2.imread(crop_path)
                if crop_image is None:
                    continue
                
                # Extract vehicle ID from crop filename first
                vehicle_id = "Unknown"
                if "ID" in crop_file:
                    try:
                        id_start = crop_file.find("ID") + 2
                        id_end = crop_file.find("_", id_start)
                        if id_end == -1:
                            id_end = crop_file.find("x", id_start)
                        vehicle_id = crop_file[id_start:id_end]
                    except:
                        vehicle_id = "Unknown"
                
                # Run helmet detection on the crop
                helmet_detections = self.perform_helmet_detection(crop_image)
                
                if helmet_detections:
                    # Check if there are any no_helmet violations
                    no_helmet_detections = [d for d in helmet_detections if 'no_helmet' in d.get('class', '').lower() or 'without' in d.get('class', '').lower()]
                    
                    # Only process and save if there are no_helmet violations
                    if no_helmet_detections:
                        # Create annotated image only for violations
                        annotated_crop = crop_image.copy()
                        
                        for detection in helmet_detections:
                            x1, y1, x2, y2 = detection['bbox']
                            confidence = detection.get('confidence', 0)
                            label = detection.get('class', 'Unknown')
                            
                            # Use neutral color for all annotations (white)
                            color = (255, 255, 255)  # White for all annotations
                            
                            # Draw bounding box with neutral color
                            cv2.rectangle(annotated_crop, (x1, y1), (x2, y2), color, 2)
                            
                            # Draw label with class name and confidence below the bounding box
                            label_text = f"{label}: {confidence:.2f}"
                            cv2.putText(annotated_crop, label_text, (x1, y2 + 20), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        
                        # Save violation image to violation folder for ImagePipeline processing
                        violation_filename = f"violation_{crop_file}"
                        violation_path = os.path.join(self.violation_dir, violation_filename)
                        cv2.imwrite(violation_path, annotated_crop)
                        
                        # Add violation record to memory (for backward compatibility)
                        violation_record = {
                            'crop_file': crop_file,
                            'violation_file': violation_filename,
                            'vehicle_id': vehicle_id,
                            'detections': no_helmet_detections,
                            'timestamp': current_time
                        }
                        self.violations.append(violation_record)
                        
                        # Store result info for violations only
                        self.helmet_results.append({
                            'crop_file': crop_file,
                            'result_file': violation_filename,
                            'detections': helmet_detections,
                            'vehicle_id': vehicle_id,
                            'timestamp': current_time
                        })
            
            # Keep only recent results (last 100)
            if len(self.helmet_results) > 100:
                self.helmet_results = self.helmet_results[-100:]
            
            # Keep only recent violations (last 200)
            if len(self.violations) > 200:
                self.violations = self.violations[-200:]
            
            self.last_helmet_analysis_time = current_time
            
        except Exception as e:
            pass
    
    def perform_vehicle_detection(self, frame):
        """Perform vehicle detection on a frame."""
        try:
            results = self.vehicle_model(frame, conf=self.confidence_threshold)
            detections = []
            
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None:
                    for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                        if int(cls) in self.vehicle_classes:
                            x1, y1, x2, y2 = box.cpu().numpy()
                            detections.append({
                                'class': 'vehicle',
                                'confidence': float(conf.cpu().numpy()),
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'center_x': (x1 + x2) / 2,
                                'center_y': (y1 + y2) / 2,
                                'width': x2 - x1,
                                'height': y2 - y1
                            })
            
            return detections
        except Exception as e:
            return []
    
    def perform_helmet_detection(self, frame):
        """Perform helmet detection on a frame."""
        try:
            results = self.helmet_model(frame, conf=self.confidence_threshold)
            detections = []
            
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None:
                    for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                        x1, y1, x2, y2 = box.cpu().numpy()
                        class_name = self.helmet_model.names[int(cls)]
                        detections.append({
                            'class': class_name,
                            'confidence': float(conf.cpu().numpy()),
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'center_x': (x1 + x2) / 2,
                            'center_y': (y1 + y2) / 2,
                            'width': x2 - x1,
                            'height': y2 - y1
                        })
            
            return detections
        except Exception as e:
            return []
    
    def perform_inference(self, frame):
        """Perform inference - now only vehicle detection, helmet detection runs separately on crops."""
        try:
            all_detections = []
            
            # Always run vehicle detection first
            vehicle_detections = self.perform_vehicle_detection(frame)
            
            # Filter by ROI if enabled
            if self.roi_enabled and self.roi_polygon:
                vehicle_detections = [d for d in vehicle_detections if self._is_detection_in_roi(d)]
            
            # Track vehicles to assign persistent IDs
            if vehicle_detections:
                vehicle_detections = self.tracker.update(vehicle_detections)
                all_detections.extend(vehicle_detections)
                
                # Auto-save vehicle crops every 1 second
                self.save_vehicle_crops(frame, vehicle_detections)
            
            # Process helmet detection on saved crops (runs in background)
            self.process_helmet_detection_on_crops()
            
            return all_detections
        except Exception as e:
            return []
    
    def draw_predictions(self, frame, predictions):
        """Draw bounding boxes and labels on the frame."""
        height, width = frame.shape[:2]
        
        # Draw ROI polygon overlay if enabled
        try:
            if self.roi_enabled and len(self.roi_polygon) >= 3:
                pts = np.array(self.roi_polygon, dtype=np.int32).reshape((-1, 1, 2))
                overlay = frame.copy()
                cv2.polylines(overlay, [pts], isClosed=True, color=(255, 255, 0), thickness=2)
                cv2.fillPoly(overlay, [pts], color=(255, 255, 0))
                # Blend overlay with transparency
                alpha = 0.12
                frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        except Exception as _:
            pass
        
        for prediction in predictions:
            try:
                # Extract coordinates (already in pixel format from YOLO)
                x1, y1, x2, y2 = prediction['bbox']
                confidence = prediction.get('confidence', 0)
                label = prediction.get('class', 'Unknown')
                
                # Skip low confidence detections
                if confidence < self.confidence_threshold:
                    continue
                
                # Ensure coordinates are within frame bounds
                x1 = max(0, min(x1, width))
                y1 = max(0, min(y1, height))
                x2 = max(0, min(x2, width))
                y2 = max(0, min(y2, height))
                
                # Choose color based on class
                if label == 'vehicle':
                    color = (0, 255, 0)  # Green for vehicles
                elif 'helmet' in label.lower():
                    color = (0, 0, 255)  # Red for helmets
                elif 'no_helmet' in label.lower() or 'without' in label.lower():
                    color = (0, 165, 255)  # Orange for no helmet
                else:
                    color = (255, 0, 0)  # Blue for other classes
                
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Compose label and optional tracking ID
                track_id = prediction.get('track_id')
                id_suffix = f" #{track_id}" if track_id is not None else ""
                # Draw label background (larger class text)
                label_text = f"{label}{id_suffix}: {confidence:.2f}"
                label_font_scale = 1.0
                label_thickness = 2
                (text_width, text_height), _ = cv2.getTextSize(
                    label_text, cv2.FONT_HERSHEY_SIMPLEX, label_font_scale, label_thickness
                )
                
                cv2.rectangle(
                    frame, 
                    (x1, y1 - text_height - 10), 
                    (x1 + text_width, y1), 
                    color, 
                    -1
                )
                
                # Draw label text
                cv2.putText(
                    frame, 
                    label_text, 
                    (x1, y1 - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    label_font_scale, 
                    (255, 255, 255), 
                    label_thickness
                )
                
                # Draw a distinct ID badge INSIDE the bounding box for vehicles
                if label == 'vehicle' and track_id is not None:
                    id_text = f"ID {track_id}"
                    (id_w, id_h), _ = cv2.getTextSize(id_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    pad = 6
                    badge_left = max(0, x1 + 2)
                    badge_top = max(0, y1 + 2)
                    badge_right = min(width, badge_left + id_w + pad)
                    badge_bottom = min(height, badge_top + id_h + pad)
                    
                    # Slightly darker badge color for readability
                    badge_color = (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
                    cv2.rectangle(frame, (badge_left, badge_top), (badge_right, badge_bottom), badge_color, -1)
                    cv2.putText(
                        frame,
                        id_text,
                        (badge_left + 3, badge_top + id_h + 1),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2
                    )
                
            except Exception as e:
                continue
        
        return frame
    
    def generate_helmet_frames(self):
        """Generate video frames showing helmet violation images from violation folder."""
        current_image_index = 0
        violation_images = []
        
        while self.is_streaming:
            try:
                # Get violation images from violation folder
                if os.path.exists(self.violation_dir):
                    violation_files = [f for f in os.listdir(self.violation_dir) 
                                     if f.lower().endswith('.jpg') and 'violation_vehicle_' in f]
                    violation_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.violation_dir, x)), reverse=True)
                    violation_images = violation_files
                
                if not violation_images:
                    # Show placeholder if no violations
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, "No helmet violations detected", (50, 240), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.putText(frame, "Waiting for violations...", (50, 280), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                else:
                    # Cycle through violation images
                    if current_image_index >= len(violation_images):
                        current_image_index = 0
                    
                    violation_file = violation_images[current_image_index]
                    violation_path = os.path.join(self.violation_dir, violation_file)
                    
                    if os.path.exists(violation_path):
                        frame = cv2.imread(violation_path)
                        if frame is not None:
                            # Resize frame to standard size
                            height, width = frame.shape[:2]
                            if width > 640 or height > 480:
                                scale = min(640/width, 480/height)
                                new_width = int(width * scale)
                                new_height = int(height * scale)
                                frame = cv2.resize(frame, (new_width, new_height))
                            
                            # Add info overlay
                            info_text = f"Helmet Violations - {len(violation_images)} total"
                            cv2.putText(frame, info_text, (10, 30), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            
                            # Add violation count
                            count_text = f"Violation {current_image_index + 1} of {len(violation_images)}"
                            cv2.putText(frame, count_text, (10, 60), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            
                            # Add timestamp
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            cv2.putText(frame, timestamp, (10, frame.shape[0] - 10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        else:
                            # Skip this image and move to next
                            current_image_index = (current_image_index + 1) % len(violation_images)
                            continue
                    else:
                        # Skip this image and move to next
                        current_image_index = (current_image_index + 1) % len(violation_images)
                        continue
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode(
                    '.jpg',
                    frame,
                    [
                        cv2.IMWRITE_JPEG_QUALITY, 80,
                        cv2.IMWRITE_JPEG_OPTIMIZE, 1
                    ]
                )
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Move to next image
                if violation_images:
                    current_image_index = (current_image_index + 1) % len(violation_images)
                
                # Update every 2 seconds
                time.sleep(2.0)
                
            except Exception as e:
                break

    # -----------------------------
    # ROI helpers and endpoints
    # -----------------------------
    def _is_detection_in_roi(self, detection):
        """Check if detection center lies inside ROI polygon."""
        try:
            if not (self.roi_enabled and self.roi_polygon and len(self.roi_polygon) >= 3):
                return True
            cx = int(detection.get('center_x', 0))
            cy = int(detection.get('center_y', 0))
            contour = np.array(self.roi_polygon, dtype=np.int32)
            # pointPolygonTest returns >0 inside, 0 on edge, <0 outside
            res = cv2.pointPolygonTest(contour, (float(cx), float(cy)), False)
            return res >= 0
        except Exception:
            return True
    
    def generate_frames(self):
        """Generate video frames with annotations."""
        frame_count = 0
        last_predictions = []
        last_detection_time = 0  # Track when last detection was performed
        detection_interval = 2.0  # Run vehicle detection every 3 seconds
        
        # Try to increase camera read performance
        if self.camera:
            try:
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 2)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
            except Exception:
                pass

        while self.is_streaming and self.camera:
            try:
                # Handle pause for video files
                if self.is_paused and self.source_type == "video":
                    time.sleep(0.1)
                    continue
                
                # Grab latest frame (drop buffer) for smoother playback
                ret = self.camera.grab()
                if ret:
                    ret, frame = self.camera.retrieve()
                if not ret:
                    # For video files, loop back to beginning
                    if self.source_type == "video" and self.total_frames > 0:
                        self.camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.current_frame = 0
                        ret, frame = self.camera.read()
                    
                    if not ret:
                        break
                
                # Update current frame for video files
                if self.source_type == "video":
                    self.current_frame = int(self.camera.get(cv2.CAP_PROP_POS_FRAMES))
                
                # Perform inference every 3 seconds
                current_time = time.time()
                if self.detection_enabled and (current_time - last_detection_time) >= detection_interval:
                    last_predictions = self.perform_inference(frame)
                    last_detection_time = current_time
                
                # Draw predictions on every frame
                if self.detection_enabled and last_predictions:
                    frame = self.draw_predictions(frame, last_predictions)
                
                # Add detection info overlay
                time_since_detection = current_time - last_detection_time if last_detection_time > 0 else 0
                next_detection_in = max(0, detection_interval - time_since_detection)
                info_text = f"Mode: {self.detection_mode} | Conf: {self.confidence_threshold:.2f} | Detections: {len(last_predictions)} | Next: {next_detection_in:.1f}s"
                cv2.putText(
                    frame, 
                    info_text, 
                    (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (255, 255, 255), 
                    2
                )
                
                # Add video info for video files
                if self.source_type == "video":
                    progress_text = f"Frame: {self.current_frame}/{self.total_frames}"
                    if self.is_paused:
                        progress_text += " [PAUSED]"
                    cv2.putText(
                        frame, 
                        progress_text, 
                        (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, 
                        (255, 255, 0), 
                        1
                    )
                
                # Add timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(
                    frame, 
                    timestamp, 
                    (10, frame.shape[0] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (255, 255, 255), 
                    1
                )
                
                # Encode frame as JPEG
                # Tune JPEG quality and enable fast encoding
                ret, buffer = cv2.imencode(
                    '.jpg',
                    frame,
                    [
                        cv2.IMWRITE_JPEG_QUALITY, 80,  # slightly lower for speed
                        cv2.IMWRITE_JPEG_OPTIMIZE, 1
                    ]
                )
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                frame_count += 1
                
                # Control frame rate based on source type
                if self.source_type == "video":
                    # Use video's original FPS
                    time.sleep(1.0 / self.fps if self.fps > 0 else 0.033)
                else:
                    # Camera: ~30 FPS
                    time.sleep(0.033)
                
            except Exception as e:
                break

# Global processor instance
processor = VideoInferenceProcessor()

@app.route('/')
def index():
    """Serve a simple test page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video Inference Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .video-container { text-align: center; margin: 20px 0; }
            .controls { margin: 20px 0; }
            button { padding: 10px 20px; margin: 5px; font-size: 16px; }
            .status { padding: 10px; background: #f0f0f0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎥 Video Inference Server</h1>
            <div class="status">
                <p><strong>Status:</strong> Server is running</p>
                <p><strong>Endpoints:</strong></p>
                <ul>
                    <li>GET /video_feed - Video stream</li>
                    <li>POST /start_stream - Start streaming</li>
                    <li>POST /stop_stream - Stop streaming</li>
                    <li>POST /toggle_detection - Toggle detection</li>
                    <li>GET /status - Get current status</li>
                </ul>
            </div>
            
            <div class="controls">
                <button onclick="startStream()">Start Stream</button>
                <button onclick="stopStream()">Stop Stream</button>
                <button onclick="toggleDetection()">Toggle Detection</button>
            </div>
            
            <div class="video-container">
                <img id="videoFeed" src="/video_feed" style="max-width: 100%; border: 2px solid #ccc;">
            </div>
        </div>
        
        <script>
            function startStream() {
                fetch('/start_stream', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => console.log(data));
            }
            
            function stopStream() {
                fetch('/stop_stream', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => console.log(data));
            }
            
            function toggleDetection() {
                fetch('/toggle_detection', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => console.log(data));
            }
        </script>
    </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    if not processor.is_streaming:
        return "Stream not started", 404
    
    return Response(
        processor.generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/helmet_feed')
def helmet_feed():
    """Helmet detection results streaming route."""
    if not processor.is_streaming:
        return "Stream not started", 404
    
    return Response(
        processor.generate_helmet_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/violation/<filename>')
def serve_violation_image(filename):
    """Serve individual violation images."""
    try:
        violation_path = os.path.join(processor.violation_dir, filename)
        if os.path.exists(violation_path):
            return send_file(violation_path, mimetype='image/jpeg')
        else:
            return "Image not found", 404
    except Exception as e:
        return f"Error serving image: {str(e)}", 500

# Add static file serving for violation directory
@app.route('/violation/')
def list_violations():
    """List available violation images."""
    try:
        if os.path.exists(processor.violation_dir):
            files = [f for f in os.listdir(processor.violation_dir) 
                    if f.lower().endswith('.jpg') and 'violation_vehicle_' in f]
            files.sort(key=lambda x: os.path.getmtime(os.path.join(processor.violation_dir, x)), reverse=True)
            return jsonify({
                'success': True,
                'files': files,
                'count': len(files)
            })
        else:
            return jsonify({
                'success': True,
                'files': [],
                'count': 0
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/start_stream', methods=['POST'])
def start_stream():
    """Start video streaming from camera or video file."""
    try:
        data = request.get_json() or {}
        source_type = data.get('source_type', 'camera')
        source = data.get('source', 0)
        
        if source_type == 'camera':
            camera_index = int(source)
            success = processor.start_source(camera_index, 'camera')
            message = f'Camera {camera_index} started successfully' if success else 'Failed to start camera'
        elif source_type == 'video':
            video_path = str(source)
            success = processor.start_source(video_path, 'video')
            message = f'Video file started successfully' if success else 'Failed to start video file'
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid source_type. Use "camera" or "video"'
            }), 400
        
        if success:
            processor.is_streaming = True
            video_info = processor.get_video_info()
            return jsonify({
                'success': True,
                'message': message,
                'video_info': video_info
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting stream: {str(e)}'
        }), 500

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    """Stop video streaming."""
    try:
        processor.stop_camera()
        return jsonify({
            'success': True,
            'message': 'Stream stopped successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping stream: {str(e)}'
        }), 500

@app.route('/toggle_detection', methods=['POST'])
def toggle_detection():
    """Toggle object detection on/off."""
    try:
        processor.detection_enabled = not processor.detection_enabled
        return jsonify({
            'success': True,
            'detection_enabled': processor.detection_enabled,
            'message': f'Detection {"enabled" if processor.detection_enabled else "disabled"}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error toggling detection: {str(e)}'
        }), 500

@app.route('/set_confidence', methods=['POST'])
def set_confidence():
    """Set confidence threshold."""
    try:
        data = request.get_json()
        threshold = data.get('threshold', 0.5)
        
        if 0 <= threshold <= 1:
            processor.confidence_threshold = threshold
            return jsonify({
                'success': True,
                'confidence_threshold': threshold,
                'message': f'Confidence threshold set to {threshold}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Threshold must be between 0 and 1'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error setting confidence: {str(e)}'
        }), 500

@app.route('/set_detection_mode', methods=['POST'])
def set_detection_mode():
    """Set the detection mode (vehicle, helmet, or both)."""
    try:
        data = request.get_json()
        mode = data.get('mode', 'vehicle')
        
        if mode in ['vehicle', 'helmet', 'both']:
            processor.detection_mode = mode
            return jsonify({
                'success': True,
                'detection_mode': mode,
                'message': f'Detection mode set to {mode}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid mode. Use "vehicle", "helmet", or "both"'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error setting detection mode: {str(e)}'
        }), 500

@app.route('/set_vehicle_classes', methods=['POST'])
def set_vehicle_classes():
    """Set the vehicle class indices to detect."""
    try:
        data = request.get_json()
        classes = data.get('classes', [0])
        
        if isinstance(classes, list) and all(isinstance(c, int) for c in classes):
            processor.vehicle_classes = classes
            return jsonify({
                'success': True,
                'vehicle_classes': classes,
                'message': f'Vehicle classes set to {classes}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Classes must be a list of integers'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error setting vehicle classes: {str(e)}'
        }), 500

@app.route('/pause_video', methods=['POST'])
def pause_video():
    """Pause video playback."""
    try:
        if processor.pause_video():
            return jsonify({
                'success': True,
                'message': 'Video paused',
                'is_paused': True
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Cannot pause (not a video file or not streaming)'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error pausing video: {str(e)}'
        }), 500

@app.route('/resume_video', methods=['POST'])
def resume_video():
    """Resume video playback."""
    try:
        if processor.resume_video():
            return jsonify({
                'success': True,
                'message': 'Video resumed',
                'is_paused': False
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Cannot resume (not a video file or not streaming)'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error resuming video: {str(e)}'
        }), 500

@app.route('/seek_video', methods=['POST'])
def seek_video():
    """Seek to specific frame in video."""
    try:
        data = request.get_json()
        frame_number = data.get('frame', 0)
        
        if processor.seek_video(frame_number):
            return jsonify({
                'success': True,
                'message': f'Seeked to frame {frame_number}',
                'current_frame': processor.current_frame
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Cannot seek (not a video file or not streaming)'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error seeking video: {str(e)}'
        }), 500

@app.route('/video_info', methods=['GET'])
def get_video_info():
    """Get current video information."""
    try:
        info = processor.get_video_info()
        if info:
            return jsonify({
                'success': True,
                'video_info': info
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No video source active'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting video info: {str(e)}'
        }), 500

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """Upload a video file for processing."""
    try:
        if 'video' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No video file provided'
            }), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Create uploads directory if it doesn't exist
        uploads_dir = 'uploads'
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save the uploaded file
        filename = file.filename
        filepath = os.path.join(uploads_dir, filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Video uploaded successfully',
            'filepath': filepath,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error uploading video: {str(e)}'
        }), 500

@app.route('/set_save_interval', methods=['POST'])
def set_save_interval():
    """Set the interval for auto-saving vehicle crops."""
    try:
        data = request.get_json()
        interval = data.get('interval', 2.0)
        
        if 0.5 <= interval <= 60:  # Between 0.5 and 60 seconds
            processor.save_interval = interval
            return jsonify({
                'success': True,
                'save_interval': interval,
                'message': f'Save interval set to {interval} seconds'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Interval must be between 0.5 and 60 seconds'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error setting save interval: {str(e)}'
        }), 500

@app.route('/set_min_crop_size', methods=['POST'])
def set_min_crop_size():
    """Set minimum crop size requirements."""
    try:
        data = request.get_json()
        min_width = 150
        min_height = 350
        
        # Validate sizes
        if 50 <= min_width <= 1000 and 50 <= min_height <= 1000:
            processor.min_crop_width = min_width
            processor.min_crop_height = min_height
            return jsonify({
                'success': True,
                'min_crop_width': min_width,
                'min_crop_height': min_height,
                'message': f'Minimum crop size set to {min_width}x{min_height}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Width and height must be between 50 and 1000 pixels'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error setting minimum crop size: {str(e)}'
        }), 500


@app.route('/crop_info', methods=['GET'])
def get_crop_info():
    """Get information about saved crops."""
    try:
        crop_files = []
        if os.path.exists(processor.cropped_images_dir):
            files = os.listdir(processor.cropped_images_dir)
            for file in files:
                if file.endswith('.jpg'):
                    filepath = os.path.join(processor.cropped_images_dir, file)
                    stat = os.stat(filepath)
                    crop_files.append({
                        'filename': file,
                        'size_kb': round(stat.st_size / 1024, 2),
                        'created': stat.st_ctime,
                        'modified': stat.st_mtime
                    })
        
        # Sort by creation time (newest first)
        crop_files.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'crop_directory': processor.cropped_images_dir,
            'total_files': len(crop_files),
            'save_interval': processor.save_interval,
            'last_save_time': processor.last_save_time,
            'files': crop_files[:50]  # Return only the 50 most recent
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting crop info: {str(e)}'
        }), 500

@app.route('/clear_crops', methods=['POST'])
def clear_crops():
    """Clear all saved crop images."""
    try:
        if os.path.exists(processor.cropped_images_dir):
            import glob
            files = glob.glob(os.path.join(processor.cropped_images_dir, "*.jpg"))
            deleted_count = 0
            
            for file in files:
                try:
                    os.remove(file)
                    deleted_count += 1
                except:
                    pass
            
            return jsonify({
                'success': True,
                'message': f'Deleted {deleted_count} crop images',
                'deleted_count': deleted_count
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No crop directory found',
                'deleted_count': 0
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error clearing crops: {str(e)}'
        }), 500

@app.route('/set_roi', methods=['POST'])
def set_roi():
    """Set or clear the ROI polygon. Payload: { enabled: bool, points: [[x,y], ...] }"""
    try:
        data = request.get_json() or {}
        enabled = bool(data.get('enabled', True))
        points = data.get('points', [])
        
        if enabled:
            if not isinstance(points, list) or len(points) < 3:
                return jsonify({ 'success': False, 'message': 'ROI requires at least 3 points' }), 400
            # Validate and clamp to positive ints
            clean_points = []
            for p in points:
                if not isinstance(p, (list, tuple)) or len(p) != 2:
                    continue
                x = int(max(0, p[0]))
                y = int(max(0, p[1]))
                clean_points.append([x, y])
            if len(clean_points) < 3:
                return jsonify({ 'success': False, 'message': 'Invalid ROI points' }), 400
            processor.roi_polygon = clean_points
            processor.roi_enabled = True
        else:
            processor.roi_polygon = []
            processor.roi_enabled = False
        
        return jsonify({
            'success': True,
            'roi': {
                'enabled': processor.roi_enabled,
                'points': processor.roi_polygon
            }
        })
    except Exception as e:
        return jsonify({ 'success': False, 'message': f'Error setting ROI: {str(e)}' }), 500

@app.route('/toggle_helmet_detection', methods=['POST'])
def toggle_helmet_detection():
    """Toggle helmet detection on/off."""
    try:
        processor.helmet_detection_enabled = not processor.helmet_detection_enabled
        return jsonify({
            'success': True,
            'helmet_detection_enabled': processor.helmet_detection_enabled,
            'message': f'Helmet detection {"enabled" if processor.helmet_detection_enabled else "disabled"}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error toggling helmet detection: {str(e)}'
        }), 500

@app.route('/helmet_results', methods=['GET'])
def get_helmet_results():
    """Get helmet detection results."""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        # Get recent results
        results = processor.helmet_results[-limit:] if processor.helmet_results else []
        
        return jsonify({
            'success': True,
            'total_results': len(processor.helmet_results),
            'results': results,
            'helmet_detection_enabled': processor.helmet_detection_enabled
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting helmet results: {str(e)}'
        }), 500

@app.route('/violations', methods=['GET'])
def get_violations():
    """Get helmet violation records."""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # Get recent violations
        violations = processor.violations[-limit:] if processor.violations else []
        
        return jsonify({
            'success': True,
            'total_violations': len(processor.violations),
            'violations': violations,
            'violation_directory': processor.violation_dir
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting violations: {str(e)}'
        }), 500

@app.route('/violation_info', methods=['GET'])
def get_violation_info():
    """Get information about saved violation images."""
    try:
        violation_files = []
        if os.path.exists(processor.violation_dir):
            files = os.listdir(processor.violation_dir)
            for file in files:
                if file.endswith('.jpg'):
                    filepath = os.path.join(processor.violation_dir, file)
                    stat = os.stat(filepath)
                    violation_files.append({
                        'filename': file,
                        'size_kb': round(stat.st_size / 1024, 2),
                        'created': stat.st_ctime,
                        'modified': stat.st_mtime
                    })
        
        # Sort by creation time (newest first)
        violation_files.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'violation_directory': processor.violation_dir,
            'total_files': len(violation_files),
            'total_violations': len(processor.violations),
            'files': violation_files[:100]  # Return only the 100 most recent
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting violation info: {str(e)}'
        }), 500

@app.route('/clear_violations', methods=['POST'])
def clear_violations():
    """Clear all saved violation images."""
    try:
        if os.path.exists(processor.violation_dir):
            import glob
            files = glob.glob(os.path.join(processor.violation_dir, "*.jpg"))
            deleted_count = 0
            
            for file in files:
                try:
                    os.remove(file)
                    deleted_count += 1
                except:
                    pass
            
            # Clear violation records
            processor.violations = []
            
            return jsonify({
                'success': True,
                'message': f'Deleted {deleted_count} violation images and cleared violation records',
                'deleted_count': deleted_count
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No violation directory found',
                'deleted_count': 0
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error clearing violations: {str(e)}'
        }), 500

@app.route('/switch_device', methods=['POST'])
def switch_device():
    """Switch between GPU and CPU."""
    try:
        data = request.get_json()
        target_device = data.get('device', 'auto')
        
        if target_device == 'auto':
            # Auto-detect best device
            processor.device = processor.detect_device()
        elif target_device in ['cpu', 'cuda:0', 'cuda:1']:
            # Force specific device
            processor.device = target_device
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid device. Use "auto", "cpu", "cuda:0", etc.'
            }), 400
        
        # Move models to new device
        processor.setup_models_on_device()
        
        device_info = processor.get_device_info()
        return jsonify({
            'success': True,
            'message': f'Switched to device: {processor.device}',
            'device_info': device_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error switching device: {str(e)}'
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get current server status."""
    video_info = processor.get_video_info()
    device_info = processor.get_device_info()
    
    # Get crop information
    crop_count = 0
    if os.path.exists(processor.cropped_images_dir):
        crop_count = len([f for f in os.listdir(processor.cropped_images_dir) if f.endswith('.jpg')])
    
    return jsonify({
        'is_streaming': processor.is_streaming,
        'detection_enabled': processor.detection_enabled,
        'confidence_threshold': processor.confidence_threshold,
        'detection_mode': processor.detection_mode,
        'vehicle_classes': processor.vehicle_classes,
        'source_available': processor.camera is not None and processor.camera.isOpened() if processor.camera else False,
        'video_info': video_info,
        'device_info': device_info,
        'crop_info': {
            'save_interval': processor.save_interval,
            'last_save_time': processor.last_save_time,
            'total_crops': crop_count,
            'crop_directory': processor.cropped_images_dir,
            'min_crop_width': processor.min_crop_width,
            'min_crop_height': processor.min_crop_height
        },
        'roi': {
            'enabled': processor.roi_enabled,
            'points': processor.roi_polygon
        },
        'helmet_detection': {
            'enabled': processor.helmet_detection_enabled,
            'total_results': len(processor.helmet_results),
            'analysis_interval': processor.helmet_analysis_interval,
            'results_directory': processor.helmet_results_dir
        },
        'violations': {
            'total_violations': len(processor.violations),
            'violation_directory': processor.violation_dir
        },
        'models_loaded': {
            'vehicle_model': 'best.pt',
            'helmet_model': 'best-helmet-2.pt'
        }
    })

# -----------------------------

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
