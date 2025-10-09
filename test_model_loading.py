#!/usr/bin/env python3
"""
Test script to verify YOLO model loading works with PyTorch 2.6.
"""

import os
import sys

def test_model_loading():
    """Test if YOLO models can be loaded successfully."""
    
    print("🧪 Testing YOLO Model Loading")
    print("=" * 40)
    
    # Check if model files exist
    model_files = ['backend/best.pt', 'backend/best-helmet-2.pt']
    
    for model_file in model_files:
        if not os.path.exists(model_file):
            print(f"❌ Model file not found: {model_file}")
            print("Please run: python setup_models.py")
            return False
        else:
            size_mb = os.path.getsize(model_file) / (1024 * 1024)
            print(f"✅ Found {model_file} ({size_mb:.1f} MB)")
    
    print("\n🔧 Applying PyTorch compatibility fixes...")
    
    try:
        import torch
        print(f"📦 PyTorch version: {torch.__version__}")
        
        # Apply fixes
        os.environ['TORCH_SERIALIZATION_WEIGHTS_ONLY'] = 'False'
        
        try:
            from ultralytics.nn.tasks import DetectionModel
            torch.serialization.add_safe_globals([DetectionModel])
            print("✅ Added safe globals")
        except:
            pass
        
        # Test loading
        print("\n🚀 Testing model loading...")
        
        from ultralytics import YOLO
        
        # Monkey patch torch.load
        original_load = torch.load
        def safe_load(*args, **kwargs):
            kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
        torch.load = safe_load
        
        # Test vehicle model
        print("📦 Loading vehicle model...")
        vehicle_model = YOLO('backend/best.pt')
        print("✅ Vehicle model loaded successfully!")
        
        # Test helmet model
        print("📦 Loading helmet model...")
        helmet_model = YOLO('backend/best-helmet-2.pt')
        print("✅ Helmet model loaded successfully!")
        
        # Restore original torch.load
        torch.load = original_load
        
        print("\n🎉 All tests passed! Models are ready to use.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nPossible solutions:")
        print("1. Update ultralytics: pip install --upgrade ultralytics")
        print("2. Downgrade PyTorch: pip install torch==2.0.1")
        print("3. Check model file integrity")
        return False

if __name__ == "__main__":
    success = test_model_loading()
    sys.exit(0 if success else 1)
