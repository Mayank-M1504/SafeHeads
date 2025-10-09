#!/bin/bash

echo "🚀 Starting Video Inference Dashboard..."
echo

echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
echo

echo "🔧 Applying PyTorch compatibility fixes..."
cd ..
python fix_pytorch_loading.py
echo

echo "🌐 Starting Flask backend server..."
python app.py &
BACKEND_PID=$!
echo "✅ Backend server starting on http://localhost:5000 (PID: $BACKEND_PID)"
echo

echo "📦 Installing frontend dependencies..."
cd ../frontend
npm install
echo

echo "⚛️ Starting React frontend..."
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend server starting on http://localhost:3000 (PID: $FRONTEND_PID)"
echo

echo "🎉 Both servers are running!"
echo "📹 Make sure your camera is connected"
echo "🌐 Open http://localhost:3000 in your browser"
echo
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait

