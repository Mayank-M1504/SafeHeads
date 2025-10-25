# Safehead Backend - Technical Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [API Endpoints](#api-endpoints)
5. [Database Schema](#database-schema)
6. [Image Processing Pipeline](#image-processing-pipeline)
7. [AI/ML Integration](#aiml-integration)
8. [Configuration Management](#configuration-management)
9. [Testing Framework](#testing-framework)
10. [Deployment & Setup](#deployment--setup)
11. [Performance Considerations](#performance-considerations)
12. [Security Features](#security-features)
13. [Troubleshooting](#troubleshooting)

---

## System Overview

The Safehead backend is a comprehensive helmet violation detection and tracking system built with Flask, OpenCV, and YOLO models. It processes real-time video streams to detect vehicles, identify helmet violations, extract number plates using OCR, and store violation records in a PostgreSQL database.

### Key Features
- **Real-time Video Processing**: Live camera feed and video file processing
- **AI-Powered Detection**: YOLO models for vehicle and helmet detection
- **OCR Integration**: Google Gemini API for number plate text extraction
- **Cloud Storage**: Cloudinary integration for image storage
- **Database Management**: PostgreSQL for violation record storage
- **RESTful API**: Comprehensive API for frontend integration
- **Parallel Processing**: Multi-threaded image processing pipeline

---

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Video Input   │───▶│  Detection API  │───▶│  Image Pipeline │
│  (Camera/File)  │    │    (app.py)     │    │ (Imagepipeline) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Violations API  │    │   Cloudinary    │
                       │(violations_api) │    │   (Storage)     │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   (Database)    │
                       └─────────────────┘
```

### Component Interaction Flow
1. **Video Capture**: Camera or video file input
2. **Vehicle Detection**: YOLO model identifies vehicles
3. **Crop Extraction**: Vehicle regions are cropped and saved
4. **Helmet Detection**: YOLO model analyzes cropped images for helmet violations
5. **OCR Processing**: Gemini API extracts number plate text
6. **Data Storage**: Violations stored in database with cloud image URLs

---

## Core Components

### 1. Main Application (`app.py`)
**Purpose**: Primary Flask application handling video streaming and real-time detection

**Key Classes**:
- `VideoInferenceProcessor`: Main processing engine
- `SimpleTracker`: IOU-based object tracking for persistent vehicle IDs

**Core Functionality**:
- **Device Management**: Automatic GPU/CPU detection and model optimization
- **Video Streaming**: Real-time video feed with MJPEG streaming
- **Object Detection**: YOLO-based vehicle and helmet detection
- **Crop Management**: Automatic saving of vehicle crops with size filtering
- **ROI Support**: Region of Interest polygon for detection filtering
- **Tracking System**: Persistent vehicle ID assignment across frames

**Key Methods**:
- `detect_device()`: Detects best available processing device (GPU/CPU)
- `perform_vehicle_detection()`: Runs YOLO vehicle detection on frames
- `perform_helmet_detection()`: Analyzes cropped images for helmet violations
- `save_vehicle_crops()`: Saves vehicle crops with timestamp and metadata
- `generate_frames()`: Creates MJPEG video stream with annotations

### 2. Violations API (`violations_api.py`)
**Purpose**: RESTful API for violation record management

**Key Features**:
- **CRUD Operations**: Create, read, update, delete violation records
- **Pagination**: Efficient data retrieval with pagination support
- **Filtering**: Search and filter violations by status, number plate
- **Statistics**: Comprehensive violation analytics and reporting
- **Export Functionality**: CSV export for data analysis
- **Cloudinary Integration**: Image upload and management

**API Endpoints**:
- `POST /api/violations`: Create new violation
- `GET /api/violations`: Retrieve violations with pagination
- `GET /api/violations/<plate>`: Get specific violation
- `PUT /api/violations/<plate>`: Update violation status
- `DELETE /api/violations/<plate>`: Delete violation and image
- `GET /api/violations/stats`: Get violation statistics
- `GET /api/violations/export`: Export violations to CSV

### 3. Database Models (`models.py`)
**Purpose**: SQLAlchemy ORM models for data persistence

**Key Model**: `Violation`
- **Primary Key**: `number_plate` (String, 20 chars)
- **Violation Details**: Type, description, timestamp
- **Image Data**: Cloudinary URL and public ID
- **Detection Metadata**: Confidence score, vehicle ID, crop filename
- **Location Data**: Location, camera ID
- **Status Management**: Active, resolved, dismissed states
- **Audit Trail**: Created/updated timestamps

### 4. Image Processing Pipeline (`Imagepipeline.py`)
**Purpose**: Parallel processing of violation images for OCR and database storage

**Key Classes**:
- `ViolationImageProcessor`: Processes individual violation images
- `ParallelImagePipeline`: Manages parallel processing workflow

**Processing Workflow**:
1. **File Monitoring**: Watches violation directory for new images
2. **Image Enhancement**: CLAHE, sharpening, normalization
3. **OCR Processing**: Gemini API for number plate extraction
4. **Validation**: Indian number plate format validation
5. **Cloud Upload**: Cloudinary integration for image storage
6. **Database Storage**: Violation record creation via API

**Key Features**:
- **Duplicate Prevention**: Tracks processed plates to avoid duplicates
- **Error Handling**: Robust error handling with retry mechanisms
- **Batch Processing**: Processes multiple images in parallel
- **Result Tracking**: JSON result files for each processed image

---

## API Endpoints

### Video Streaming Endpoints
- `GET /video_feed`: Live video stream with detections
- `GET /helmet_feed`: Helmet violation images stream
- `POST /start_stream`: Start video streaming
- `POST /stop_stream`: Stop video streaming
- `POST /toggle_detection`: Enable/disable detection
- `POST /set_confidence`: Set detection confidence threshold
- `POST /set_detection_mode`: Set detection mode (vehicle/helmet/both)

### Video Control Endpoints
- `POST /pause_video`: Pause video playback
- `POST /resume_video`: Resume video playback
- `POST /seek_video`: Seek to specific frame
- `GET /video_info`: Get video information
- `POST /upload_video`: Upload video file for processing

### Detection Configuration
- `POST /set_vehicle_classes`: Set vehicle class indices
- `POST /set_roi`: Set Region of Interest polygon
- `POST /toggle_helmet_detection`: Enable/disable helmet detection
- `POST /set_save_interval`: Set crop save interval
- `POST /set_min_crop_size`: Set minimum crop size requirements

### Data Management
- `GET /crop_info`: Get crop information and statistics
- `POST /clear_crops`: Clear all saved crops
- `GET /helmet_results`: Get helmet detection results
- `GET /violations`: Get violation records
- `GET /violation_info`: Get violation image information
- `POST /clear_violations`: Clear violation records

### System Status
- `GET /status`: Get comprehensive system status
- `POST /switch_device`: Switch between GPU/CPU
- `GET /violation/<filename>`: Serve individual violation images

---

## Database Schema

### Violations Table
```sql
CREATE TABLE violations (
    number_plate VARCHAR(20) PRIMARY KEY,
    violation_type VARCHAR(50) NOT NULL,
    violation_description TEXT,
    image_url VARCHAR(500) NOT NULL,
    image_public_id VARCHAR(200),
    violation_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT,
    vehicle_id VARCHAR(50),
    crop_filename VARCHAR(200),
    location VARCHAR(200),
    camera_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active'
);
```

### Indexes
- Primary key on `number_plate`
- Index on `violation_timestamp` for time-based queries
- Index on `status` for status filtering
- Index on `created_at` for pagination

---

## Image Processing Pipeline

### Processing Stages

#### 1. File Detection
- **Monitoring**: Polls violation directory every 2 seconds
- **Filtering**: Only processes `violation_vehicle_*.jpg` files
- **Deduplication**: Tracks processed files to avoid reprocessing

#### 2. Image Enhancement
- **CLAHE**: Contrast Limited Adaptive Histogram Equalization
- **Sharpening**: Unsharp mask filter for text clarity
- **Normalization**: Histogram stretching for brightness
- **Denoising**: Fast non-local means denoising

#### 3. OCR Processing
- **Model Selection**: Tries multiple Gemini models in order of preference
- **Prompt Engineering**: Specialized prompts for Indian number plates
- **Format Validation**: Regex validation for Indian plate format
- **Error Handling**: Graceful fallback for OCR failures

#### 4. Data Storage
- **Cloud Upload**: Cloudinary integration with folder organization
- **Database Storage**: Violation record creation via REST API
- **Result Tracking**: JSON files for processing results

### Configuration Parameters
- **Minimum Resolution**: 200x400 pixels
- **Polling Interval**: 2 seconds
- **Plate Validation**: 8-10 character Indian format
- **Duplicate Prevention**: Normalized plate text tracking

---

## AI/ML Integration

### YOLO Models
- **Vehicle Detection**: `best.pt` - Custom trained for vehicle detection
- **Helmet Detection**: `helmetv3.pt` - Custom trained for helmet/no-helmet classification

### Model Loading
- **Safe Loading**: Handles PyTorch 2.6 compatibility issues
- **Device Optimization**: Automatic GPU/CPU detection and optimization
- **Memory Management**: Efficient model loading and memory usage

### OCR Integration
- **Google Gemini API**: Multiple model fallback system
- **Model Priority**: 
  1. `gemini-2.0-flash` (latest fast model)
  2. `gemini-2.0-flash-001` (stable 2.0)
  3. `gemini-2.5-flash` (latest 2.5)
  4. `gemini-2.0-pro-exp` (experimental pro)
  5. `gemini-2.5-pro` (latest pro)
  6. `gemini-1.5-flash` (fallback)
  7. `gemini-1.5-pro` (fallback)
  8. `gemini-pro` (legacy)

### Detection Pipeline
1. **Vehicle Detection**: YOLO identifies vehicles in video frames
2. **Crop Extraction**: Vehicle regions are cropped and saved
3. **Helmet Analysis**: YOLO analyzes crops for helmet violations
4. **OCR Processing**: Gemini extracts number plate text
5. **Validation**: Format validation and duplicate checking

---

## Configuration Management

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# OCR Configuration
GEMINI_API_KEY=your_gemini_api_key

# API Configuration
VIOLATIONS_API_URL=http://localhost:5001
VIOLATIONS_API_PORT=5001

# Flask Configuration
SECRET_KEY=your_secret_key
```

### Configuration Classes
- **`Config`**: Main configuration class with environment variable loading
- **`CloudinaryService`**: Cloudinary-specific configuration and operations

### Setup Scripts
- **`create_env.py`**: Interactive environment file creation
- **`setup_database.py`**: Database setup and connection testing
- **`init_db.py`**: Database initialization and table creation

---

## Testing Framework

### Test Files
1. **`test_database.py`**: Database connection and operations testing
2. **`test_gemini.py`**: Gemini API connection and model testing
3. **`test_pipeline.py`**: Image pipeline component testing
4. **`test_validation.py`**: Number plate validation testing
5. **`test_violations_api.py`**: Violations API endpoint testing

### Test Coverage
- **Database Operations**: CRUD operations, connection testing
- **API Endpoints**: All REST endpoints with various scenarios
- **OCR Integration**: Model availability and response testing
- **Image Processing**: Pipeline component functionality
- **Data Validation**: Number plate format validation

### Running Tests
```bash
# Run all tests
python test_database.py
python test_gemini.py
python test_pipeline.py
python test_validation.py
python test_violations_api.py
```

---

## Deployment & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- CUDA-compatible GPU (optional)
- Cloudinary account
- Google Gemini API key

### Installation Steps
1. **Clone Repository**: Download the codebase
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Environment Setup**: Run `python create_env.py`
4. **Database Setup**: Run `python setup_database.py`
5. **Test Configuration**: Run test scripts
6. **Start Services**: Run `python start_all_services.py`

### Service Management
- **Main App**: `python app.py` (Port 5000)
- **Violations API**: `python violations_api.py` (Port 5001)
- **Image Pipeline**: `python start_image_pipeline.py`

### Docker Support
- **Database**: PostgreSQL container
- **Application**: Flask application container
- **Volume Mounts**: For persistent data storage

---

## Performance Considerations

### Optimization Strategies
- **GPU Acceleration**: Automatic CUDA detection and optimization
- **Model Caching**: YOLO models loaded once and reused
- **Batch Processing**: Parallel image processing pipeline
- **Memory Management**: Efficient crop size filtering
- **Connection Pooling**: Database connection optimization

### Resource Requirements
- **CPU**: Multi-core processor recommended
- **RAM**: 8GB+ recommended for smooth operation
- **GPU**: NVIDIA GPU with CUDA support (optional but recommended)
- **Storage**: SSD recommended for faster I/O

### Performance Monitoring
- **Frame Rate**: Configurable FPS for video processing
- **Detection Interval**: Adjustable detection frequency
- **Crop Size Limits**: Minimum size requirements for processing
- **Memory Usage**: GPU/CPU memory monitoring

---

## Security Features

### Data Protection
- **Environment Variables**: Sensitive data in .env files
- **Database Security**: PostgreSQL authentication and authorization
- **API Security**: Input validation and sanitization
- **Image Privacy**: Secure cloud storage with access controls

### Access Control
- **Database Access**: User-based authentication
- **API Endpoints**: RESTful API with proper HTTP methods
- **File System**: Secure file handling and cleanup
- **Cloud Storage**: Cloudinary access controls

### Error Handling
- **Graceful Degradation**: System continues operation on errors
- **Logging**: Comprehensive error logging and monitoring
- **Recovery**: Automatic retry mechanisms for failed operations
- **Validation**: Input validation and sanitization

---

## Troubleshooting

### Common Issues

#### 1. Model Loading Errors
- **PyTorch Compatibility**: Update ultralytics or downgrade PyTorch
- **CUDA Issues**: Check GPU drivers and CUDA installation
- **Memory Issues**: Reduce batch size or use CPU

#### 2. Database Connection Issues
- **PostgreSQL Not Running**: Start PostgreSQL service
- **Connection String**: Verify DATABASE_URL format
- **Permissions**: Check database user permissions

#### 3. OCR Failures
- **API Key**: Verify GEMINI_API_KEY is correct
- **Model Availability**: Check Gemini API status
- **Image Quality**: Ensure images meet minimum resolution

#### 4. Cloudinary Issues
- **Credentials**: Verify Cloudinary credentials
- **Network**: Check internet connectivity
- **Quota**: Monitor Cloudinary usage limits

### Debug Tools
- **Test Scripts**: Comprehensive testing suite
- **Logging**: Detailed error logging
- **Status Endpoints**: System health monitoring
- **Configuration Validation**: Environment variable checking

### Performance Issues
- **GPU Memory**: Monitor GPU memory usage
- **CPU Usage**: Check CPU utilization
- **Disk I/O**: Monitor file system performance
- **Network**: Check API response times

---

## Conclusion

The Safehead backend system provides a comprehensive solution for helmet violation detection and tracking. With its modular architecture, robust error handling, and extensive testing framework, it offers a reliable platform for traffic safety enforcement. The system's AI/ML integration, cloud storage capabilities, and RESTful API make it suitable for both standalone deployment and integration with larger traffic management systems.

The documentation covers all major aspects of the system, from high-level architecture to detailed implementation specifics. This should provide developers and system administrators with the information needed to understand, deploy, maintain, and extend the Safehead backend system.

