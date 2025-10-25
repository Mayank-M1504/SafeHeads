import os
import re
import cv2
import numpy as np
from PIL import Image
from collections import defaultdict
import time
import json
import threading
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import requests

# Load environment variables
load_dotenv()

# =============================
# CONFIGURATION
# =============================
# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, "violation")      # Folder containing violation images
MIN_RESOLUTION = 200 * 400  # Minimum width*height allowed (e.g., 400x400)
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "processed")  # Folder for processed images
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")      # Folder for analysis results

# OCR Model Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ OCR model configured successfully")
else:
    print("⚠️  OCR API key not found. Set GEMINI_API_KEY in .env file")

# Database and Cloudinary Configuration
VIOLATIONS_API_URL = os.getenv('VIOLATIONS_API_URL', 'http://localhost:5001')
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', '')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', '')

# Enhanced prompt for number plate reading including two-line plates

PLATE_READING_PROMPT = """
Look at this image and extract ONLY the number plate text.

CRITICAL REQUIREMENTS:
1. The number plate must be COMPLETELY VISIBLE in the image
2. The number plate must follow this exact Indian format:
   - 2 alphabets + 2 digits + 1 or 2 alphabets + 3 or 4 digits
   - Example: MH12AB1234 or KA01CD567

3. The number plate may be in one line or two lines
4. If it's a two-line number plate, combine both lines into a single line of text

VALIDATION RULES:
- If the number plate is partially hidden, cut off, or obscured, return "incomplete_plate"
- If the number plate is too blurry or unclear to read accurately, return "unreadable"
- If the number plate does not match the Indian format (2 letters + 2 digits + 1-2 letters + 3-4 digits), return "invalid_format"
- If no number plate is visible in the image, return "no_plate_visible"
- If the number plate is too small or low resolution to read clearly, return "low_quality"

ONLY return the complete, clearly visible number plate text if it meets ALL requirements above.
Do not guess or make up number plate text.
Do not include any other information or analysis.
Do not read Number plates of Vehicle other than Scooter or Bike.
"""

# Number plate validation settings
MIN_PLATE_LENGTH = 8  # Minimum characters for a valid Indian number plate
MAX_PLATE_LENGTH = 20  # Maximum characters for a valid Indian number plate (increased for two-line plates)

def normalize_plate_text(plate_text):
    """Normalize number plate text by removing dashes, spaces, newlines, and converting to uppercase."""
    if not plate_text or plate_text.lower() in ['unreadable', 'error', 'gemini_not_configured', 'incomplete_plate', 'no_plate_visible', 'low_quality']:
        return None
    
    # Remove dashes, spaces, newlines, and convert to uppercase
    normalized = plate_text.replace('-', '').replace(' ', '').replace('\n', '').replace('\r', '').upper()
    return normalized

def is_valid_plate(plate_text):
    """Check if the plate text is valid and follows Indian number plate format."""
    normalized = normalize_plate_text(plate_text)
    
    if not normalized:
        return False
    
    # Check for invalid responses from OCR
    if normalized in ['UNREADABLE', 'INVALID_FORMAT', 'ERROR', 'OCR_NOT_CONFIGURED', 'INCOMPLETE_PLATE', 'NO_PLATE_VISIBLE', 'LOW_QUALITY']:
        return False
    
    # Check length (Indian plates are typically 8-10 characters)
    if len(normalized) < 8 or len(normalized) > 10:
        return False
    
    # Check Indian number plate format: 2 letters + 2 digits + 1-2 letters + 3-4 digits
    import re
    pattern = r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{3,4}$'
    
    if not re.match(pattern, normalized):
        return False
    
    return True

def upload_to_cloudinary(image_path, public_id):
    """Upload image to Cloudinary and return URL and public_id."""
    if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
        print("⚠️ Cloudinary credentials not configured")
        print(f"   Cloud Name: {CLOUDINARY_CLOUD_NAME}")
        print(f"   API Key: {'*' * len(CLOUDINARY_API_KEY) if CLOUDINARY_API_KEY else 'Not set'}")
        print(f"   API Secret: {'*' * len(CLOUDINARY_API_SECRET) if CLOUDINARY_API_SECRET else 'Not set'}")
        return None
    
    try:
        import cloudinary
        import cloudinary.uploader
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )
        
        print(f"☁️ Cloudinary configured for cloud: {CLOUDINARY_CLOUD_NAME}")
        print(f"📁 Uploading image: {image_path}")
        
        # Upload image
        result = cloudinary.uploader.upload(
            image_path,
            folder="violations",
            public_id=public_id,
            resource_type="image"
        )
        
        print(f"✅ Upload successful!")
        print(f"   URL: {result.get('url')}")
        print(f"   Public ID: {result.get('public_id')}")
        
        return {
            'url': result.get('url'),
            'public_id': result.get('public_id')
        }
        
    except Exception as e:
        print(f"❌ Error uploading to Cloudinary: {e}")
        print(f"   Image path: {image_path}")
        print(f"   Public ID: {public_id}")
        return None

def save_violation_to_database(violation_data):
    """Save violation data to the violations database via API."""
    try:
        print(f"📡 Sending violation data to API: {VIOLATIONS_API_URL}/api/violations")
        print(f"📊 Data: {violation_data['number_plate']} - {violation_data['image_url']}")
        
        response = requests.post(
            f"{VIOLATIONS_API_URL}/api/violations",
            json=violation_data,
            timeout=10
        )
        
        print(f"📡 API Response: {response.status_code}")
        
        if response.status_code == 201:
            print(f"✅ Violation saved to database: {violation_data['number_plate']}")
            return True
        else:
            print(f"❌ Failed to save violation: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        print(f"   API URL: {VIOLATIONS_API_URL}/api/violations")
        return False


# =============================
# FILENAME PARSING
# =============================
FILENAME_REGEX = re.compile(r"violation_vehicle_.*?_ID(\d+)_([0-9]+)x([0-9]+)_conf([0-9.]+)_nohelmets(\d+)\.jpg", re.IGNORECASE)

def parse_filename(filename):
    match = FILENAME_REGEX.match(filename)
    if not match:
        return None
    vehicle_id = match.group(1)
    width, height = int(match.group(2)), int(match.group(3))
    confidence = float(match.group(4))
    no_helmet_count = int(match.group(5))
    resolution = width * height
    return vehicle_id, width, height, confidence, resolution, no_helmet_count


# =============================
# OCR NUMBER PLATE READING
# =============================
def read_number_plate_with_ocr(image_path):
    """Read number plate using OCR model."""
    if not GEMINI_API_KEY:
        return "ocr_not_configured"
    
    # Try different model names in order of preference (newest first)
    model_names = [
        'gemini-2.0-flash',           # Latest fast model
        'gemini-2.0-flash-001',       # Stable 2.0 flash
        'gemini-2.5-flash',           # Latest 2.5 flash
        'gemini-2.0-pro-exp',         # Latest pro model
        'gemini-2.5-pro',             # Latest 2.5 pro
        'gemini-1.5-flash',           # Fallback to 1.5
        'gemini-1.5-pro',             # Fallback to 1.5 pro
        'gemini-pro'                  # Legacy fallback
    ]
    
    for model_name in model_names:
        try:
            print(f"🤖 Trying OCR model: {model_name}")
            
            # Load the image
            img = Image.open(image_path)
            
            # Initialize OCR model
            model = genai.GenerativeModel(model_name)
            
            # Analyze the image
            response = model.generate_content([PLATE_READING_PROMPT, img])
            
            # Get the response text
            plate_text = response.text.strip()
            
            print(f"✅ Successfully used model: {model_name}")
            
            # Clean up the response
            plate_text_lower = plate_text.lower().strip()
            
            # Check for specific error responses
            if any(error in plate_text_lower for error in ['unreadable', 'incomplete_plate', 'no_plate_visible', 'low_quality', 'invalid_format']):
                return plate_text_lower
            
            # Remove any extra text and return just the plate
            lines = plate_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 3:  # Basic validation
                    return line
            
            return "unreadable"
            
        except Exception as e:
            print(f"⚠️ Model {model_name} failed: {e}")
            continue
    
    # If all models failed
    print(f"❌ All OCR models failed for {image_path}")
    return "error"

# =============================
# IMAGE PROCESSOR CLASS
# =============================
class ViolationImageProcessor:
    def __init__(self):
        self.processed_files = set()
        self.results = []
        self.seen_plates = set()  # Track normalized plates to avoid duplicates
        
        # Create directories
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        os.makedirs(RESULTS_DIR, exist_ok=True)
        
        print("🔍 Image processor initialized")
    
    def check_for_new_files(self):
        """Check for new violation images in the directory."""
        if not os.path.exists(BASE_DIR):
            return []
        
        current_files = set()
        for filename in os.listdir(BASE_DIR):
            if filename.lower().endswith('.jpg') and 'violation_vehicle_' in filename:
                current_files.add(filename)
        
        # Find new files
        new_files = current_files - self.processed_files
        return list(new_files)
    
    def process_violation_image(self, image_path, filename):
        """Process a single violation image."""
        try:
            print(f"🔄 Processing new violation image: {filename}")
            
            # Parse filename to get vehicle info
            parsed = parse_filename(filename)
            if not parsed:
                print(f"⚠️ Could not parse filename: {filename}")
                return
            
            vehicle_id, width, height, confidence, resolution, no_helmet_count = parsed
            
            # Check minimum resolution
            if resolution < MIN_RESOLUTION:
                print(f"⏭️ Skipping {filename}: resolution too low ({width}x{height})")
                return
            
            # Read number plate with OCR using original image
            print(f"🤖 Reading number plate with OCR...")
            plate_text = read_number_plate_with_ocr(image_path)
            print(f"🔖 Raw plate text: {plate_text}")
            
            # Validate and normalize plate text
            normalized_plate = normalize_plate_text(plate_text)
            
            if not is_valid_plate(plate_text):
                print(f"❌ Invalid plate: '{plate_text}' (normalized: '{normalized_plate}') - Skipping")
                # Still mark as processed to avoid reprocessing
                self.processed_files.add(filename)
                return
            
            # Check for duplicates
            if normalized_plate in self.seen_plates:
                print(f"🔄 Duplicate plate detected: '{plate_text}' (normalized: '{normalized_plate}') - Skipping")
                # Still mark as processed to avoid reprocessing
                self.processed_files.add(filename)
                return
            
            # Add to seen plates
            self.seen_plates.add(normalized_plate)
            
            # Only process valid plates for database storage
            print(f"✅ Valid plate detected: '{plate_text}' (normalized: '{normalized_plate}') - Processing for database...")
            
            # Upload to Cloudinary
            public_id = f"violation_{int(time.time())}_{vehicle_id}"
            print(f"☁️ Uploading image to Cloudinary with public_id: {public_id}")
            cloudinary_result = upload_to_cloudinary(image_path, public_id)
            
            if cloudinary_result:
                print(f"✅ Cloudinary upload successful: {cloudinary_result['url']}")
                # Prepare violation data for database
                violation_data = {
                    'number_plate': normalized_plate,
                    'violation_type': 'no_helmet',
                    'violation_description': f'Helmet violation detected - {no_helmet_count} person(s) without helmet',
                    'image_url': cloudinary_result['url'],
                    'image_public_id': cloudinary_result['public_id'],
                    'violation_timestamp': datetime.fromtimestamp(time.time()).isoformat(),
                    'confidence_score': confidence,
                    'vehicle_id': vehicle_id,
                    'crop_filename': filename,
                    'no_helmet_count': no_helmet_count,
                    'location': 'Unknown',  # Can be enhanced later
                    'camera_id': 'Unknown',  # Can be enhanced later
                    'status': 'active'
                }
                
                print(f"📊 Violation data prepared: {violation_data['number_plate']} - {violation_data['image_url']}")
                
                # Save to database
                if save_violation_to_database(violation_data):
                    print(f"💾 Violation data saved to database successfully")
                else:
                    print(f"⚠️ Failed to save violation data to database")
            else:
                print(f"❌ Failed to upload image to Cloudinary, skipping database save")
            
            # Create result record
            result = {
                'original_file': filename,
                'vehicle_id': vehicle_id,
                'resolution': f"{width}x{height}",
                'confidence': confidence,
                'no_helmet_count': no_helmet_count,
                'plate_text': plate_text,
                'normalized_plate': normalized_plate,
                'ocr_source': 'original_image',  # Indicates OCR was performed on original image
                'timestamp': time.time(),
                'processed_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Save result to JSON
            result_filename = filename.replace('.jpg', '_result.json')
            result_path = os.path.join(RESULTS_DIR, result_filename)
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Add to results list
            self.results.append(result)
            
            # Mark file as processed
            self.processed_files.add(filename)
            
            # Keep only last 1000 results
            if len(self.results) > 1000:
                self.results = self.results[-1000:]
            
            print(f"✅ Processing complete: {filename}")
            print(f"   🔖 Plate: '{plate_text}' → '{normalized_plate}'")
            print(f"   🚫 No-helmets: {no_helmet_count}")
            print(f"   📄 Result saved: {result_filename}")
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            # Still mark as processed to avoid infinite retries
            self.processed_files.add(filename)

# =============================
# PARALLEL PIPELINE CLASS
# =============================
class ParallelImagePipeline:
    def __init__(self):
        self.processor = None
        self.is_running = False
        self.poll_interval = 2.0  # Check every 2 seconds
        
    def start(self):
        """Start the parallel image processing pipeline."""
        if self.is_running:
            print("⚠️ Pipeline is already running")
            return
        
        print("🚀 Starting Parallel Image Processing Pipeline...")
        print(f"📁 Monitoring directory: {BASE_DIR}")
        print(f"📁 Processed images: {PROCESSED_DIR}")
        print(f"📁 Results: {RESULTS_DIR}")
        print(f"⏱️ Polling interval: {self.poll_interval} seconds")
        
        # Create directories
        os.makedirs(BASE_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        os.makedirs(RESULTS_DIR, exist_ok=True)
        
        # Initialize processor
        self.processor = ViolationImageProcessor()
        self.is_running = True
        
        print("✅ Pipeline started successfully!")
        
        # OCR model is ready
        if GEMINI_API_KEY:
            print("✅ OCR model ready for processing")
        else:
            print("⚠️ OCR model not configured")
        
        print("🔍 Polling for new violation images...")
        
        # Process any existing images
        self.process_existing_images()
        
    def stop(self):
        """Stop the parallel image processing pipeline."""
        if not self.is_running:
            print("⚠️ Pipeline is not running")
            return
        
        print("🛑 Stopping Parallel Image Processing Pipeline...")
        self.is_running = False
        print("✅ Pipeline stopped successfully!")
        
    def run_polling_loop(self):
        """Run the main polling loop."""
        while self.is_running:
            try:
                # Check for new files
                new_files = self.processor.check_for_new_files()
                
                if new_files:
                    print(f"📋 Found {len(new_files)} new files to process")
                    for filename in new_files:
                        file_path = os.path.join(BASE_DIR, filename)
                        if os.path.exists(file_path):
                            # Wait a moment for file to be fully written
                            time.sleep(0.5)
                            self.processor.process_violation_image(file_path, filename)
                
                # Sleep before next check
                time.sleep(self.poll_interval)
                
            except Exception as e:
                print(f"❌ Error in polling loop: {e}")
                time.sleep(self.poll_interval)
    
    def process_existing_images(self):
        """Process any existing violation images in the directory."""
        if not os.path.exists(BASE_DIR):
            return
        
        existing_files = [f for f in os.listdir(BASE_DIR) 
                         if f.lower().endswith('.jpg') and 'violation_vehicle_' in f]
        
        if existing_files:
            print(f"📋 Found {len(existing_files)} existing images to process...")
            for filename in existing_files:
                file_path = os.path.join(BASE_DIR, filename)
                if os.path.exists(file_path):
                    self.processor.process_violation_image(file_path, filename)
        else:
            print("📋 No existing images found")
    
    def get_results(self, limit=50):
        """Get recent processing results."""
        if not self.processor:
            return []
        return self.processor.results[-limit:] if self.processor.results else []
    
    def get_status(self):
        """Get pipeline status."""
        unique_plates = len(self.processor.seen_plates) if self.processor else 0
        return {
            'is_running': self.is_running,
            'monitored_directory': BASE_DIR,
            'processed_directory': PROCESSED_DIR,
            'results_directory': RESULTS_DIR,
            'total_processed': len(self.processor.results) if self.processor else 0,
            'unique_plates': unique_plates,
            'gemini_configured': bool(GEMINI_API_KEY),
            'poll_interval': self.poll_interval,
            'validation_settings': {
                'min_plate_length': MIN_PLATE_LENGTH,
                'max_plate_length': MAX_PLATE_LENGTH
            }
        }

# =============================
# MAIN EXECUTION
# =============================
def main():
    """Main function to run the parallel pipeline."""
    pipeline = ParallelImagePipeline()
    
    try:
        # Start the pipeline
        pipeline.start()
        
        # Run the polling loop
        print("\n🔄 Pipeline is running... Press Ctrl+C to stop")
        pipeline.run_polling_loop()
            
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal...")
        pipeline.stop()
        print("👋 Pipeline stopped. Goodbye!")

if __name__ == "__main__":
    main()