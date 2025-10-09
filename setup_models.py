#!/usr/bin/env python3
"""
Setup script to copy YOLO model files to the backend directory.
Run this script to ensure the model files are in the correct location.
"""

import os
import shutil
import sys

def setup_models():
    """Copy model files to backend directory if they exist."""
    
    # Model files to look for
    model_files = {
        'best.pt': 'Vehicle detection model',
        'best-helmet-2.pt': 'Helmet detection model'
    }
    
    backend_dir = 'backend'
    
    # Create backend directory if it doesn't exist
    if not os.path.exists(backend_dir):
        os.makedirs(backend_dir)
        print(f"✅ Created {backend_dir} directory")
    
    print("🔍 Looking for YOLO model files...")
    
    for model_file, description in model_files.items():
        # Check if model exists in current directory
        if os.path.exists(model_file):
            target_path = os.path.join(backend_dir, model_file)
            
            # Copy if not already in backend directory or if source is newer
            if not os.path.exists(target_path) or os.path.getmtime(model_file) > os.path.getmtime(target_path):
                shutil.copy2(model_file, target_path)
                print(f"✅ Copied {model_file} to {backend_dir}/ ({description})")
            else:
                print(f"✅ {model_file} already up to date in {backend_dir}/")
        else:
            print(f"⚠️  {model_file} not found in current directory ({description})")
            print(f"   Please ensure {model_file} is in the project root directory")
    
    # Check if models exist in backend directory
    print("\n📁 Checking backend directory for models...")
    missing_models = []
    
    for model_file in model_files.keys():
        backend_path = os.path.join(backend_dir, model_file)
        if os.path.exists(backend_path):
            size_mb = os.path.getsize(backend_path) / (1024 * 1024)
            print(f"✅ {model_file} found in backend/ ({size_mb:.1f} MB)")
        else:
            missing_models.append(model_file)
            print(f"❌ {model_file} missing from backend/")
    
    if missing_models:
        print(f"\n⚠️  Missing models: {', '.join(missing_models)}")
        print("Please ensure these model files are available before running the server.")
        return False
    else:
        print("\n🎉 All model files are ready!")
        print("You can now start the backend server with: python backend/app.py")
        return True

if __name__ == "__main__":
    print("🚀 YOLO Model Setup Script")
    print("=" * 40)
    
    success = setup_models()
    
    if not success:
        print("\n❌ Setup incomplete. Please add missing model files.")
        sys.exit(1)
    else:
        print("\n✅ Setup complete!")
        sys.exit(0)

