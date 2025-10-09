@echo off
echo 🚀 Starting Video Inference Dashboard...
echo.

echo 📦 Installing backend dependencies...
cd backend
pip install -r requirements.txt
echo.

echo 🔧 Applying PyTorch compatibility fixes...
cd ..
python fix_pytorch_loading.py
echo.

echo 🤖 Checking Gemini AI configuration...
if not exist backend\.env (
    echo ⚠️  WARNING: .env file not found!
    echo To enable Gemini AI analysis:
    echo 1. Create .env file in backend directory
    echo 2. Add: GEMINI_API_KEY=your_api_key_here
    echo 3. Get API key from: https://makersuite.google.com/app/apikey
    echo.
) else (
    echo ✅ .env file found
)
echo.

echo 🌐 Starting Flask backend server...
start "Backend Server" cmd /k "python app.py"
echo ✅ Backend server starting on http://localhost:5000
echo.

echo 📦 Installing frontend dependencies...
cd ..\frontend
call npm install
echo.

echo ⚛️ Starting React frontend...
start "Frontend Server" cmd /k "npm run dev"
echo ✅ Frontend server starting on http://localhost:3000
echo.

echo 🎉 Both servers are starting!
echo 📹 Make sure your camera is connected
echo 🌐 Open http://localhost:3000 in your browser
echo.
pause

