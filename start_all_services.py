#!/usr/bin/env python3
"""
Startup script for all Safehead services.
This runs:
1. Main backend (app.py) on port 5000
2. Violations API (violations_api.py) on port 5001  
3. Image Pipeline (Imagepipeline.py) for processing violations
4. Frontend (React) on port 3000
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def run_backend():
    """Run the main backend on port 5000."""
    print("🚀 Starting Main Backend (Port 5000)...")
    try:
        subprocess.run([sys.executable, "backend/app.py"], check=True)
    except KeyboardInterrupt:
        print("🛑 Main Backend stopped")
    except Exception as e:
        print(f"❌ Error in Main Backend: {e}")

def run_violations_api():
    """Run the violations API on port 5001."""
    print("🚀 Starting Violations API (Port 5001)...")
    try:
        subprocess.run([sys.executable, "backend/violations_api.py"], check=True)
    except KeyboardInterrupt:
        print("🛑 Violations API stopped")
    except Exception as e:
        print(f"❌ Error in Violations API: {e}")

def run_image_pipeline():
    """Run the image pipeline."""
    print("🚀 Starting Image Pipeline...")
    try:
        subprocess.run([sys.executable, "backend/Imagepipeline.py"], check=True)
    except KeyboardInterrupt:
        print("🛑 Image Pipeline stopped")
    except Exception as e:
        print(f"❌ Error in Image Pipeline: {e}")

def run_frontend():
    """Run the React frontend on port 3000."""
    print("🚀 Starting Frontend (Port 3000)...")
    try:
        os.chdir("frontend")
        subprocess.run(["npm", "run", "dev"], check=True)
    except KeyboardInterrupt:
        print("🛑 Frontend stopped")
    except Exception as e:
        print(f"❌ Error in Frontend: {e}")

def main():
    """Start all services."""
    print("=" * 60)
    print("🚀 SAFEHEAD - Starting All Services")
    print("=" * 60)
    print("📊 Main Backend:     http://localhost:5000")
    print("🗄️  Violations API:   http://localhost:5001")
    print("🤖 Image Pipeline:   Processing violations")
    print("🎨 Frontend:         http://localhost:3000")
    print("=" * 60)
    print()
    
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Start all services in separate threads
    threads = []
    
    # Start main backend
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    threads.append(backend_thread)
    time.sleep(2)  # Give backend time to start
    
    # Start violations API
    violations_thread = threading.Thread(target=run_violations_api, daemon=True)
    violations_thread.start()
    threads.append(violations_thread)
    time.sleep(2)  # Give violations API time to start
    
    # Start image pipeline
    pipeline_thread = threading.Thread(target=run_image_pipeline, daemon=True)
    pipeline_thread.start()
    threads.append(pipeline_thread)
    time.sleep(2)  # Give pipeline time to start
    
    # Start frontend
    frontend_thread = threading.Thread(target=run_frontend, daemon=True)
    frontend_thread.start()
    threads.append(frontend_thread)
    
    print("✅ All services started!")
    print("🌐 Open http://localhost:3000 in your browser")
    print("⏹️  Press Ctrl+C to stop all services")
    print()
    
    try:
        # Wait for all threads
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
