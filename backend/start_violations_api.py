#!/usr/bin/env python3
"""
Startup script for the Violations API backend.
This runs the violations database management API on port 5001.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the violations API backend."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Starting Violations API Backend...")
    print("📍 Port: 5001")
    print("🔗 URL: http://localhost:5001")
    print("📊 Database: PostgreSQL")
    print("☁️  Cloudinary: Image storage")
    print("-" * 50)
    
    try:
        # Run the violations API
        subprocess.run([sys.executable, "violations_api.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Violations API stopped by user")
    except Exception as e:
        print(f"❌ Error starting Violations API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
