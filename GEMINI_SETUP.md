# 🤖 Gemini AI Integration Setup

## 📋 Prerequisites

1. **Get Gemini API Key**:
   - Visit: https://makersuite.google.com/app/apikey
   - Create a new API key
   - Copy the API key

## ⚙️ Configuration

### Method 1: Environment File (.env)

1. Create a `.env` file in the `backend/` directory:
   ```bash
   cd backend
   touch .env
   ```

2. Add your Gemini API key to the `.env` file:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### Method 2: System Environment Variable

```bash
export GEMINI_API_KEY=your_actual_api_key_here
```

## 🚀 Usage

Once configured, the system will automatically:

1. **Analyze Saved Vehicle Crops**: Every saved vehicle image gets analyzed
2. **Extract Vehicle Information**: 
   - Vehicle type (car, truck, motorcycle, etc.)
   - Color
   - Brand (if visible)
   - License plate (if visible)
   - Condition assessment
   - Safety concerns
   - Special features

3. **Background Processing**: Analysis runs in background without affecting video performance

## 📊 API Endpoints

- `POST /toggle_gemini_analysis` - Enable/disable analysis
- `GET /gemini_results` - Get analysis results
- `POST /analyze_image` - Analyze specific image
- `GET /status` - Check Gemini configuration status

## 🔧 Troubleshooting

### "Gemini API key not found"
- Check your `.env` file exists in `backend/` directory
- Verify the API key is correctly set
- Restart the backend server

### "Gemini AI not configured"
- Ensure you have a valid API key
- Check your internet connection
- Verify the API key has proper permissions

### Analysis not working
- Check server console for error messages
- Verify images are being saved properly
- Check Gemini API quota limits

## 💡 Pre-decided Analysis Prompt

The system uses this prompt for vehicle analysis:

```
Analyze this vehicle image and provide the following information in JSON format:

{
  "vehicle_type": "car/truck/motorcycle/bus/van/other",
  "color": "primary color of the vehicle",
  "brand": "estimated brand if visible (or 'unknown')",
  "license_plate": "license plate text if visible (or 'not_visible')",
  "condition": "good/fair/poor/damaged",
  "special_features": ["list", "of", "notable", "features"],
  "estimated_year": "estimated year range (e.g., '2015-2020') or 'unknown'",
  "safety_concerns": ["list", "any", "visible", "safety", "issues"],
  "confidence": "high/medium/low based on image quality"
}
```

## 📈 Performance Notes

- Analysis runs in background (doesn't slow video processing)
- Uses thread pool for concurrent analysis
- Results are cached in memory
- Typical analysis time: 2-5 seconds per image
