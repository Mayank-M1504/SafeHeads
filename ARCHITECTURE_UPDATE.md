# Safehead Architecture Update

## Overview
The Safehead system has been restructured to improve performance and scalability by separating concerns into multiple specialized services.

## New Architecture

### 🏗️ **Service Separation**

#### 1. **Main Backend (Port 5000)**
- **File**: `backend/app.py`
- **Purpose**: Video processing, vehicle detection, helmet detection
- **Responsibilities**:
  - Camera/video streaming
  - YOLO model inference
  - Real-time detection and tracking
  - Saving violation images to `violation/` folder
  - **No database operations** (removed for performance)

#### 2. **Violations API (Port 5001)**
- **File**: `backend/violations_api.py`
- **Purpose**: Database management and violation data API
- **Responsibilities**:
  - PostgreSQL database operations
  - Cloudinary image management
  - CRUD operations for violations
  - Statistics and reporting
  - CSV export functionality

#### 3. **Image Pipeline (Background Process)**
- **File**: `backend/Imagepipeline.py`
- **Purpose**: Process violation images and extract number plates
- **Responsibilities**:
  - Monitor `violation/` folder for new images
  - Use Gemini AI for number plate extraction
  - **Only save valid, complete number plates** to database
  - Upload images to Cloudinary
  - Send data to Violations API

#### 4. **Frontend (Port 3000)**
- **File**: `frontend/src/App.jsx`
- **Purpose**: User interface
- **Responsibilities**:
  - Video streaming display
  - Violation management interface
  - Calls both backends as needed

## 🔄 **Data Flow**

```
1. Video Stream → Main Backend (Port 5000)
   ↓
2. Helmet Detection → Save to violation/ folder
   ↓
3. Image Pipeline → Process violation images
   ↓
4. Gemini AI → Extract number plates
   ↓
5. Valid Plates → Upload to Cloudinary
   ↓
6. Violations API (Port 5001) → Save to database
   ↓
7. Frontend → Display violations from database
```

## 🚀 **Key Improvements**

### **Performance Benefits**
- **Reduced Main Backend Load**: Database operations moved to separate service
- **No Stuttering**: Main backend focuses only on real-time processing
- **Parallel Processing**: Image pipeline runs independently
- **Scalable**: Each service can be scaled independently

### **Data Quality**
- **Only Valid Plates**: Images with incomplete/unreadable plates are not stored
- **Gemini AI Integration**: Advanced OCR for number plate extraction
- **Duplicate Prevention**: Avoids storing duplicate violations

### **Separation of Concerns**
- **Main Backend**: Real-time video processing
- **Violations API**: Data management and persistence
- **Image Pipeline**: AI processing and validation
- **Frontend**: User interface

## 📁 **File Structure**

```
Safehead/
├── backend/
│   ├── app.py                    # Main backend (Port 5000)
│   ├── violations_api.py         # Violations API (Port 5001)
│   ├── Imagepipeline.py          # Image processing pipeline
│   ├── config.py                 # Configuration (removed from app.py)
│   ├── models.py                 # Database models
│   ├── cloudinary_service.py     # Cloudinary integration
│   └── requirements.txt          # Dependencies
├── frontend/
│   └── src/App.jsx              # Updated to call both APIs
├── start_all_services.py        # Start all services
└── ARCHITECTURE_UPDATE.md       # This file
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/safehead_violations

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Violations API
VIOLATIONS_API_URL=http://localhost:5001
VIOLATIONS_API_PORT=5001
```

## 🚀 **Starting the System**

### **Option 1: Start All Services**
```bash
python start_all_services.py
```

### **Option 2: Start Services Individually**
```bash
# Terminal 1: Main Backend
python backend/app.py

# Terminal 2: Violations API
python backend/violations_api.py

# Terminal 3: Image Pipeline
python backend/Imagepipeline.py

# Terminal 4: Frontend
cd frontend && npm run dev
```

## 🔍 **API Endpoints**

### **Main Backend (Port 5000)**
- `GET /` - Health check
- `POST /start_stream` - Start video stream
- `POST /stop_stream` - Stop video stream
- `POST /upload_video` - Upload video file
- `GET /violations` - Get recent violations (memory only)

### **Violations API (Port 5001)**
- `GET /api/violations` - Get all violations (paginated)
- `POST /api/violations` - Create violation
- `GET /api/violations/<number_plate>` - Get specific violation
- `PUT /api/violations/<number_plate>` - Update violation
- `DELETE /api/violations/<number_plate>` - Delete violation
- `GET /api/violations/stats` - Get statistics
- `GET /api/violations/export` - Export to CSV

## 🎯 **Benefits of New Architecture**

1. **Performance**: Main backend no longer stutters during database operations
2. **Scalability**: Each service can be scaled independently
3. **Reliability**: Service failures don't affect the entire system
4. **Data Quality**: Only valid, complete number plates are stored
5. **Maintainability**: Clear separation of responsibilities
6. **Development**: Easier to work on individual components

## 🔧 **Troubleshooting**

### **Common Issues**
1. **Port Conflicts**: Ensure ports 5000, 5001, and 3000 are available
2. **Database Connection**: Check PostgreSQL is running and credentials are correct
3. **Cloudinary**: Verify API credentials are set
4. **Gemini AI**: Ensure API key is configured for number plate extraction

### **Service Dependencies**
- Violations API requires PostgreSQL
- Image Pipeline requires Gemini AI API key
- All services require proper environment variables

## 📊 **Monitoring**

- **Main Backend**: Check video streaming and detection performance
- **Violations API**: Monitor database operations and response times
- **Image Pipeline**: Watch for new violation images and processing status
- **Frontend**: Ensure API calls are working correctly

This architecture provides a robust, scalable foundation for the Safehead violation detection system while maintaining high performance and data quality.
