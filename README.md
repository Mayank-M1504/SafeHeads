# 🛡️ Safehead - AI-Powered Helmet Detection & Number Plate Recognition System

A comprehensive real-time video streaming application with AI-powered object detection, featuring vehicle detection, helmet detection, and automated number plate recognition. The system includes a Flask backend for video processing, a React frontend for user interaction, and a parallel image processing pipeline for violation analysis.

## 🌟 Key Features

### 🎥 Real-time Video Processing
- **Live Camera Streaming**: MJPEG video streaming with real-time controls
- **Dual AI Detection**: Vehicle detection (`best.pt`) and helmet detection (`best-helmet-2.pt`)
- **Time-based Inference**: Configurable detection intervals (e.g., every 3 seconds)
- **Multiple Detection Modes**: Vehicle only, helmet only, or both simultaneously

### 🚗 Vehicle & Violation Management
- **Automatic Vehicle Cropping**: Saves detected vehicle regions with metadata
- **Violation Detection**: Identifies vehicles without helmets
- **Smart Image Processing**: Parallel pipeline for violation image enhancement
- **Number Plate Recognition**: AI-powered OCR for text extraction

### 🔍 Advanced Image Processing
- **Image Enhancement**: CLAHE, sharpening, and brightness normalization
- **YOLO-based Alignment**: Number plate detection for image alignment
- **Exposure Fusion**: Merges multiple images for better quality
- **Duplicate Detection**: Prevents processing the same number plate multiple times

### 📊 Data Management
- **Structured Storage**: Organized directories for violations, processed images, and results
- **JSON Results**: Detailed metadata including timestamps, confidence scores, and plate text
- **Validation System**: Ensures only complete and valid number plates are processed
- **Git Integration**: Proper `.gitignore` for generated files and models

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────┐    HTTP/WebSocket    ┌─────────────────┐
│   React Frontend │ ◄─────────────────► │  Flask Backend  │
│   (Port 3000)    │                     │   (Port 5000)   │
└─────────────────┘                     └─────────────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │  Camera Input   │
                                        │   + Local YOLO  │
                                        │   Models        │
                                        └─────────────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │ Violation Images│
                                        │   (violation/)  │
                                        └─────────────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │Parallel Pipeline│
                                        │(Imagepipeline.py)│
                                        └─────────────────┘
```

### Detailed Data Flow Diagram
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SAFEHEAD SYSTEM FLOW                              │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Camera    │───►│   Flask     │───►│  YOLO       │───►│ Violation   │
│   Input     │    │  Backend    │    │ Detection   │    │  Images     │
│  (Video)    │    │ (app.py)    │    │ (3 sec)     │    │(violation/) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                    │
                                                                    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   OCR       │◄───│  Enhanced   │◄───│  Parallel   │◄───│  File       │
│   Engine    │    │   Images    │    │  Pipeline   │    │ Monitor     │
│ (Text Extr) │    │(processed/) │    │(Imagepipeline)│   │ (Polling)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Results   │    │  Image      │    │  YOLO       │    │  React      │
│   (JSON)    │    │ Enhancement │    │ Plate       │    │ Frontend    │
│(results/)   │    │ (CLAHE,     │    │ Detection   │    │ (Port 3000) │
│             │    │  Sharp)     │    │ (Alignment) │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Number Plate Processing Flow
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        NUMBER PLATE PROCESSING PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Violation   │───►│  Filename   │───►│  Image      │───►│  YOLO       │
│   Image     │    │  Parsing    │    │ Enhancement │    │ Detection   │
│ (violation/)│    │(ID, Res,    │    │(CLAHE,      │    │(Plate BB)   │
│             │    │ Conf)       │    │ Sharp)      │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                    │
                                                                    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   JSON      │◄───│   OCR       │◄───│  Plate      │◄───│  Image      │
│  Results    │    │   Engine    │    │ Validation  │    │ Alignment   │
│(results/)   │    │ (Text Extr) │    │(Length,     │    │(Plate Ctr)  │
│             │    │             │    │ Content)    │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Duplicate  │    │  Normalize  │    │  Enhanced   │    │  Raw Model  │
│  Check      │    │  Plate Text │    │   Image     │    │   Output    │
│(Skip if     │    │(Remove -)   │    │(processed/) │    │(All Classes)│
│ Exists)     │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Parallel Processing Pipeline
```
┌─────────────────────────────────────────────────────────────┐
│                Parallel Image Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│ 1. Monitor violation/ directory for new images             │
│ 2. Parse filename for vehicle ID, resolution, confidence   │
│ 3. Enhance image (CLAHE, sharpening, normalization)        │
│ 4. Detect number plate using YOLO model                    │
│ 5. Read plate text using OCR engine                        │
│ 6. Validate and normalize plate text                       │
│ 7. Check for duplicates                                    │
│ 8. Save enhanced image and results                         │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Webcam or camera device
- YOLO model files (`best.pt` and `best-helmet-2.pt`)
- OCR API key (for number plate recognition)
- CUDA-compatible GPU (optional, for faster inference)

### Environment Setup

1. **Create environment file:**
   ```bash
   # Create .env file in backend directory
   echo "OCR_API_KEY=your_ocr_api_key_here" > backend/.env
   ```

2. **YOLO model files are included in the repository:**
   - `best.pt` (vehicle detection model)
   - `best-helmet-2.pt` (helmet detection model)
   - `yolov8n.pt` (YOLOv8 nano model)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Flask server:**
   ```bash
   python app.py
   ```
   The backend will be available at: `http://localhost:5000`

4. **Start the parallel image pipeline (in a separate terminal):**
   ```bash
   python Imagepipeline.py
   ```
   Or use the helper script:
   ```bash
   python run_pipeline.py
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   The frontend will be available at: `http://localhost:3000`

## 🎛️ Usage

### Starting the Complete System

1. **Start Backend** (Terminal 1):
   ```bash
   cd backend
   python app.py
   ```

2. **Start Image Pipeline** (Terminal 2):
   ```bash
   cd backend
   python Imagepipeline.py
   ```

3. **Start Frontend** (Terminal 3):
   ```bash
   cd frontend
   npm run dev
   ```

4. **Open Dashboard** at `http://localhost:3000`

### Controls Available

- **Stream Controls**: Start/Stop video streaming
- **Detection Toggle**: Enable/disable AI inference
- **Detection Mode**: Choose between Vehicle, Helmet, or Both
- **Confidence Threshold**: Adjust detection sensitivity (0.0 - 1.0)
- **Vehicle Classes**: Configure which YOLO classes to detect as vehicles
- **Camera Index**: Select different camera devices
- **Inference Interval**: Set time between detections (e.g., 3 seconds)

## 📁 Project Structure

```
Safehead/
├── backend/
│   ├── app.py                    # Main Flask application
│   ├── Imagepipeline.py          # Parallel image processing pipeline
│   ├── run_pipeline.py           # Helper script to run pipeline
│   ├── test_gemini.py            # Gemini API testing script
│   ├── test_validation.py        # Number plate validation testing
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # Environment variables (create this)
│   ├── .gitignore               # Backend-specific git ignore
│   ├── violation/               # Violation images (auto-created)
│   ├── processed/               # Enhanced images (auto-created)
│   ├── results/                 # JSON results (auto-created)
│   ├── cropped/                 # Vehicle crops (auto-created)
│   └── uploads/                 # Uploaded videos (auto-created)
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main React component
│   │   ├── main.jsx             # React entry point
│   │   └── index.css            # Styling
│   ├── package.json             # Node.js dependencies
│   ├── vite.config.js           # Vite configuration
│   └── index.html               # HTML template
├── .gitignore                   # Root git ignore file
├── best.pt                      # Vehicle detection model (included)
├── best-helmet-2.pt            # Helmet detection model (included)
├── yolov8n.pt                  # YOLOv8 nano model (included)
└── README.md                    # This file
```

## 🔧 Configuration

### Backend Configuration

Edit `backend/app.py` to modify:

```python
# Detection settings
DETECTION_INTERVAL = 3  # seconds between detections
CONFIDENCE_THRESHOLD = 0.5
VEHICLE_CLASSES = [2, 3, 5, 7]  # YOLO class indices for vehicles

# Camera settings
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
```

### Image Pipeline Configuration

Edit `backend/Imagepipeline.py` to modify:

```python
# Pipeline settings
BASE_DIR = "violation"           # Folder containing violation images
TOP_N_IMAGES = 2                 # Number of images to merge per vehicle
MIN_RESOLUTION = 200 * 400       # Minimum width*height allowed
PLATE_MODEL_PATH = "best.pt"     # Path to the vehicle/number plate detection model
PLATE_CONFIDENCE = 0.5           # Confidence threshold for plate detection
PROCESSED_DIR = "processed"      # Directory for enhanced images
RESULTS_DIR = "results"          # Directory for Gemini results

# Number plate validation
MIN_PLATE_LENGTH = 8             # Minimum characters for valid plate
MAX_PLATE_LENGTH = 15            # Maximum characters for valid plate
```

### Frontend Configuration

Edit `frontend/src/App.jsx` to modify:

```javascript
// Backend URL
const API_BASE_URL = 'http://localhost:5000';

// Default settings
const DEFAULT_CONFIDENCE = 0.5;
const DEFAULT_INFERENCE_INTERVAL = 3; // seconds
```

## 🔍 API Endpoints

### Main Backend (Flask)

- `GET /video_feed` - MJPEG video stream
- `POST /start_stream` - Start camera capture
- `POST /stop_stream` - Stop camera capture
- `POST /toggle_detection` - Toggle AI detection
- `POST /set_confidence` - Set confidence threshold
- `POST /set_detection_mode` - Change detection mode
- `POST /set_vehicle_classes` - Configure vehicle class indices
- `POST /set_inference_interval` - Set time between detections
- `GET /status` - Get current system status

### Image Pipeline

The image pipeline runs independently and processes files automatically. It provides:

- **Automatic Processing**: Monitors `violation/` directory for new images
- **Enhanced Images**: Saves processed images to `processed/` directory
- **JSON Results**: Saves detailed results to `results/` directory
- **Duplicate Prevention**: Tracks processed number plates to avoid duplicates

## 🧪 Testing

### Test Number Plate Validation

```bash
cd backend
python test_validation.py
```

This will test the validation functions with various plate formats:
- Valid plates with dashes and spaces
- Invalid plates (too short, too long, only numbers, only letters)
- Error cases (unreadable, empty)

### Test OCR API Connection

```bash
cd backend
python test_gemini.py
```

This will:
- Test OCR API connectivity
- List available models
- Show which models are working
- Help debug API issues

### Test Image Pipeline

```bash
cd backend
python Imagepipeline.py
```

This will:
- Start the parallel processing pipeline
- Monitor the `violation/` directory
- Process any existing violation images
- Show real-time processing logs

### Test Complete System

1. **Start all components** (3 terminals):
   ```bash
   # Terminal 1: Backend
   cd backend && python app.py
   
   # Terminal 2: Image Pipeline
   cd backend && python Imagepipeline.py
   
   # Terminal 3: Frontend
   cd frontend && npm run dev
   ```

2. **Test workflow**:
   - Open `http://localhost:3000`
   - Start video stream
   - Enable detection
   - Wait for violations to be detected
   - Check `violation/`, `processed/`, and `results/` directories

## 🔧 Troubleshooting

### Common Issues

1. **"Camera not found"**
   - Check camera index (try 0, 1, 2...)
   - Ensure camera is not used by another application
   - Check camera permissions

2. **"Server Offline"**
   - Verify Flask server is running on port 5000
   - Check firewall settings
   - Ensure all dependencies are installed

3. **"OCR API errors"**
   - Verify `OCR_API_KEY` is set in `.env` file
   - Check API key validity and quota
   - Run `python test_gemini.py` to test connection
   - The system automatically tries multiple OCR models if one fails

4. **"PyTorch loading errors"**
   - The system includes automatic fixes for PyTorch 2.6+ compatibility
   - If issues persist, try downgrading PyTorch or updating ultralytics
   - Check that model files are in the correct location

5. **"No detections"**
   - Lower confidence threshold
   - Check if objects match the model's training data
   - Verify model files are in the correct location
   - Adjust inference interval (try 1-5 seconds)

6. **"Image pipeline not processing"**
   - Ensure `violation/` directory exists
   - Check that images follow the naming convention
   - Verify OCR API key is configured
   - Check pipeline logs for specific errors

7. **"Duplicate plates being processed"**
   - This should not happen with the new validation system
   - Check that the pipeline is running correctly
   - Verify that `seen_plates` tracking is working

8. **"Invalid plates being saved"**
   - The system now validates all plates before saving
   - Check validation settings in `Imagepipeline.py`
   - Run `python test_validation.py` to test validation logic

### Performance Optimization

- **Reduce inference frequency**: Modify `DETECTION_INTERVAL` in backend
- **Lower resolution**: Adjust camera settings
- **GPU acceleration**: Install OpenCV with CUDA support
- **Pipeline optimization**: Adjust `TOP_N_IMAGES` and `MIN_RESOLUTION` settings

## 🔐 Security Notes

- **API Keys**: Keep your Gemini API key secure in `.env` file
- **Network**: Use HTTPS in production
- **CORS**: Configure CORS properly for production
- **Camera Access**: Be mindful of privacy when using cameras
- **Data Storage**: Violation images may contain sensitive information

## 📊 Data Formats

### Violation Image Naming Convention

```
violation_vehicle_{timestamp}_ID{vehicle_id}_{width}x{height}_conf{confidence}.jpg
```

Example: `violation_vehicle_1760025204085_ID15_414x714_conf0.58.jpg`

### JSON Results Format

```json
{
  "original_file": "violation_vehicle_1760025204085_ID15_414x714_conf0.58.jpg",
  "enhanced_file": "violation_vehicle_1760025204085_ID15_414x714_conf0.58_enhanced.jpg",
  "vehicle_id": "15",
  "resolution": "414x714",
  "confidence": 0.58,
  "plate_text": "KA-55 X 599",
  "normalized_plate": "KA55X599",
  "timestamp": 1760027914.0697322,
  "processed_at": "2025-10-09 22:08:34"
}
```

## 🚀 Advanced Features

### Number Plate Validation & Deduplication

The system includes sophisticated validation and deduplication:

- **Length Validation**: Ensures plates are between 8-15 characters
- **Content Validation**: Requires both letters and numbers
- **Normalization**: Removes dashes and spaces for comparison (e.g., "KA-55 X 599" → "KA55X599")
- **Duplicate Detection**: Prevents processing the same plate multiple times
- **Error Handling**: Skips unreadable, incomplete, or invalid plates
- **Smart Filtering**: Automatically rejects plates that are too short, too long, or contain only letters/numbers

#### Validation Examples:
```
✅ Valid Plates:
- "KA-55 X 599" → "KA55X599" (normalized)
- "MH12AB1234" → "MH12AB1234"
- "DL01CD5678" → "DL01CD5678"

❌ Invalid Plates (Skipped):
- "KA-55" (too short)
- "unreadable" (Gemini couldn't read)
- "123456789" (only numbers)
- "ABCDEFGH" (only letters)
- "KA-55 X 599 EXTRA LONG" (too long)
```

### Image Enhancement Pipeline

- **CLAHE**: Contrast Limited Adaptive Histogram Equalization
- **Sharpening**: Unsharp mask filter for better clarity
- **Normalization**: Brightness and contrast adjustment
- **Denoising**: Noise reduction for better OCR results

### Parallel Processing

- **Independent Operation**: Pipeline runs separately from main backend
- **Real-time Monitoring**: Polls for new images every 2 seconds
- **Error Recovery**: Continues processing even if individual images fail
- **Resource Management**: Limits memory usage and result storage

## 📋 Recent Changes & Improvements

### Version 2.0 - Enhanced Number Plate Processing

#### New Features:
- **Parallel Image Processing Pipeline**: Independent processing of violation images
- **Number Plate Validation**: Smart validation and deduplication system
- **Enhanced Image Processing**: CLAHE, sharpening, and normalization
- **YOLO-based Alignment**: Number plate detection for better image alignment
- **OCR Integration**: Automated number plate text recognition
- **Comprehensive Testing**: Validation and API testing scripts

#### Key Improvements:
- **Time-based Detection**: Configurable inference intervals (e.g., every 3 seconds)
- **Duplicate Prevention**: Tracks processed plates to avoid reprocessing
- **Error Handling**: Robust error handling for API failures and model loading
- **PyTorch Compatibility**: Automatic fixes for PyTorch 2.6+ compatibility issues
- **Git Integration**: Proper `.gitignore` for generated files and models

#### Technical Enhancements:
- **Modular Architecture**: Separated concerns between video processing and image analysis
- **Real-time Monitoring**: Polling-based file monitoring for new violation images
- **Structured Data**: JSON results with comprehensive metadata
- **Resource Management**: Memory-efficient processing with result limits

### Migration from Version 1.0:
- **OCR Integration**: Moved from backend to parallel pipeline
- **Image Processing**: Enhanced from simple cropping to full enhancement pipeline
- **Validation**: Added comprehensive plate validation and deduplication
- **Architecture**: Separated video processing from image analysis

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📞 Support

For issues related to:
- **OCR API**: Check your OCR service documentation
- **YOLO Models**: Verify ultralytics installation
- **Camera issues**: Verify OpenCV installation
- **React/Vite**: Check Node.js version compatibility
- **Flask**: Ensure Python dependencies are correct

---

**Happy coding! 🚀**