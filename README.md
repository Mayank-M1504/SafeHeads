# 🎥 Video Inference Dashboard

A real-time video streaming application with AI-powered object detection using local YOLO models. Features vehicle detection and helmet detection with a Flask backend for video processing and a React frontend for user interaction.

## 🌟 Features

- **Real-time Video Streaming**: Live camera feed with MJPEG streaming
- **Dual AI Detection**: Vehicle detection (`best.pt`) and helmet detection (`best-helmet-2.pt`)
- **Multiple Detection Modes**: Vehicle only, helmet only, or both simultaneously
- **Interactive Dashboard**: Modern React interface with real-time controls
- **GPU Acceleration**: Automatic CUDA support for faster inference
- **Configurable Settings**: Adjust confidence thresholds, detection modes, and camera settings
- **Responsive Design**: Works on desktop and mobile devices
- **Color-coded Annotations**: Green for vehicles, red for helmets, orange for no helmet
- **Vehicle Crop Saving**: Automatically saves detected vehicle regions

## 🏗️ Architecture

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
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Webcam or camera device
- YOLO model files (`best.pt` and `best-helmet-2.pt`)
- CUDA-compatible GPU (optional, for faster inference)

### Model Setup

1. **Place your YOLO model files in the project root:**
   - `best.pt` (vehicle detection model)
   - `best-helmet-2.pt` (helmet detection model)

2. **Run the model setup script:**
   ```bash
   python setup_models.py
   ```

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

### Starting Video Stream

1. **Open the dashboard** at `http://localhost:3000`
2. **Check server status** - should show "Server Online"
3. **Configure camera index** (usually 0 for default camera)
4. **Click "Start Stream"** to begin video capture
5. **Toggle detection** on/off as needed

### Controls Available

- **Stream Controls**: Start/Stop video streaming
- **Detection Toggle**: Enable/disable AI inference
- **Detection Mode**: Choose between Vehicle, Helmet, or Both
- **Confidence Threshold**: Adjust detection sensitivity (0.0 - 1.0)
- **Vehicle Classes**: Configure which YOLO classes to detect as vehicles
- **Camera Index**: Select different camera devices

### API Endpoints

The backend provides several REST endpoints:

- `GET /video_feed` - MJPEG video stream
- `POST /start_stream` - Start camera capture
- `POST /stop_stream` - Stop camera capture
- `POST /toggle_detection` - Toggle AI detection
- `POST /set_confidence` - Set confidence threshold
- `POST /set_detection_mode` - Change detection mode (vehicle/helmet/both)
- `POST /set_vehicle_classes` - Configure vehicle class indices
- `GET /status` - Get current system status

## ⚙️ Configuration

### Backend Configuration

Edit `backend/app.py` to modify:

```python
# Default API key
api_key = "FRLSmhx5mDHuvYQTmLID"

# Default model
model_id = "bike-detection-yxesm/1"

# Camera settings
camera_width = 640
camera_height = 480
camera_fps = 30
```

### Frontend Configuration

Edit `frontend/src/App.jsx` to modify:

```javascript
// Backend URL
const API_BASE_URL = 'http://localhost:5000';

// Default settings
const DEFAULT_CONFIDENCE = 0.5;
const DEFAULT_MODEL = 'bike-detection-yxesm/1';
```

## 🎨 Customization

### Adding New Models

1. **Get model ID** from Roboflow
2. **Update model** via the frontend interface
3. **Or modify** the backend default model

### Styling Changes

The frontend uses CSS custom properties for easy theming:

```css
:root {
  --primary-color: #4ecdc4;
  --secondary-color: #ff6b6b;
  --background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
}
```

### Camera Settings

Modify camera resolution and FPS in `backend/app.py`:

```python
self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
self.camera.set(cv2.CAP_PROP_FPS, 60)
```

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

3. **"No detections"**
   - Lower confidence threshold
   - Check if objects match the model's training data
   - Verify Roboflow API key is valid

4. **Poor performance**
   - Reduce camera resolution
   - Increase inference interval
   - Close other applications using camera/CPU

### Performance Optimization

- **Reduce inference frequency**: Modify `inference_interval` in backend
- **Lower resolution**: Adjust camera settings
- **GPU acceleration**: Install OpenCV with CUDA support
- **Model optimization**: Use lighter Roboflow models

## 📁 Project Structure

```
├── backend/
│   ├── app.py              # Flask server with video processing
│   ├── requirements.txt    # Python dependencies
│   └── temp_frame.jpg     # Temporary inference file
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Main React component
│   │   ├── main.jsx       # React entry point
│   │   └── index.css      # Styling
│   ├── package.json       # Node.js dependencies
│   ├── vite.config.js     # Vite configuration
│   └── index.html         # HTML template
└── README.md              # This file
```

## 🔐 Security Notes

- **API Key**: Keep your Roboflow API key secure
- **Network**: Use HTTPS in production
- **CORS**: Configure CORS properly for production
- **Camera Access**: Be mindful of privacy when using cameras

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📞 Support

For issues related to:
- **Roboflow API**: Check Roboflow documentation
- **Camera issues**: Verify OpenCV installation
- **React/Vite**: Check Node.js version compatibility
- **Flask**: Ensure Python dependencies are correct

---

**Happy coding! 🚀**
