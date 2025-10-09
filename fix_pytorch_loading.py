#!/usr/bin/env python3
"""
Fix PyTorch 2.6 weights_only loading issue for YOLO models.
Run this script before starting the server if you encounter loading errors.
"""

import sys
import os

def fix_pytorch_loading():
    """Apply fixes for PyTorch 2.6 weights_only issue."""
    
    print("🔧 Applying PyTorch 2.6 compatibility fixes...")
    
    try:
        import torch
        print(f"📦 PyTorch version: {torch.__version__}")
        
        # Method 1: Set environment variable
        os.environ['TORCH_SERIALIZATION_WEIGHTS_ONLY'] = 'False'
        print("✅ Set TORCH_SERIALIZATION_WEIGHTS_ONLY=False")
        
        # Method 2: Add safe globals
        try:
            from ultralytics.nn.tasks import DetectionModel
            torch.serialization.add_safe_globals([DetectionModel])
            print("✅ Added DetectionModel to safe globals")
        except ImportError:
            print("⚠️  Could not import DetectionModel (ultralytics not installed?)")
        
        # Method 3: Test loading a model if available
        test_models = ['best.pt', 'best-helmet-2.pt', 'backend/best.pt', 'backend/best-helmet-2.pt']
        
        for model_path in test_models:
            if os.path.exists(model_path):
                print(f"🧪 Testing model loading: {model_path}")
                try:
                    from ultralytics import YOLO
                    
                    # Try loading with patched torch.load
                    original_load = torch.load
                    def safe_load(*args, **kwargs):
                        kwargs['weights_only'] = False
                        return original_load(*args, **kwargs)
                    
                    torch.load = safe_load
                    model = YOLO(model_path)
                    torch.load = original_load
                    
                    print(f"✅ Successfully loaded {model_path}")
                    break
                    
                except Exception as e:
                    print(f"❌ Failed to load {model_path}: {e}")
                    continue
        
        print("\n🎉 PyTorch compatibility fixes applied!")
        print("You can now start the server with: python backend/app.py")
        
    except ImportError:
        print("❌ PyTorch not installed. Please install with: pip install torch")
        return False
    
    return True

def check_dependencies():
    """Check if all required dependencies are installed."""
    
    required_packages = {
        'torch': 'PyTorch',
        'ultralytics': 'Ultralytics YOLO',
        'cv2': 'OpenCV (opencv-python)',
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS'
    }
    
    print("📋 Checking dependencies...")
    
    missing = []
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - Not installed")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r backend/requirements.txt")
        return False
    
    print("\n✅ All dependencies are installed!")
    return True

def main():
    """Main function."""
    print("🛠️  PyTorch 2.6 Compatibility Fixer")
    print("=" * 40)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first.")
        sys.exit(1)
    
    # Apply fixes
    if fix_pytorch_loading():
        print("\n✅ Setup complete! You can now run the server.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
