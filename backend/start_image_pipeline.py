#!/usr/bin/env python3
"""
Startup script for the Image Pipeline.
This runs the ImagePipeline.py which processes violation images and saves them to the database.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the image pipeline."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Starting Image Pipeline...")
    print("📁 Monitoring: violation/ directory")
    print("🤖 AI: Gemini API for number plate reading")
    print("💾 Database: Violations API (port 5001)")
    print("☁️  Cloudinary: Image upload")
    print("-" * 50)
    
    try:
        # Run the image pipeline
        subprocess.run([sys.executable, "Imagepipeline.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Image Pipeline stopped by user")
    except Exception as e:
        print(f"❌ Error starting Image Pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
