#!/usr/bin/env python3
"""
GPU Diagnostic Script for YOLO Model Inference
Checks GPU availability, CUDA installation, and PyTorch GPU support.
"""

import sys
import os

def check_gpu_availability():
    """Comprehensive GPU diagnostic check."""
    
    print("🔍 GPU Diagnostic Report")
    print("=" * 50)
    
    # Check PyTorch installation and CUDA support
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"✅ PyTorch CUDA compiled: {torch.version.cuda}")
        
        # Check CUDA availability
        cuda_available = torch.cuda.is_available()
        print(f"{'✅' if cuda_available else '❌'} CUDA available: {cuda_available}")
        
        if cuda_available:
            device_count = torch.cuda.device_count()
            print(f"✅ GPU devices found: {device_count}")
            
            # List all available GPUs
            for i in range(device_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_props = torch.cuda.get_device_properties(i)
                gpu_memory = gpu_props.total_memory / 1024**3
                
                print(f"\n🎮 GPU {i}: {gpu_name}")
                print(f"   Memory: {gpu_memory:.1f} GB")
                print(f"   Compute Capability: {gpu_props.major}.{gpu_props.minor}")
                print(f"   Multi-processors: {gpu_props.multi_processor_count}")
                
                # Test GPU functionality
                try:
                    test_tensor = torch.randn(1000, 1000).to(f'cuda:{i}')
                    result = torch.mm(test_tensor, test_tensor)
                    print(f"   ✅ GPU {i} test: PASSED")
                except Exception as e:
                    print(f"   ❌ GPU {i} test: FAILED - {e}")
        else:
            print("\n❌ No CUDA GPUs available")
            print("Possible reasons:")
            print("  - NVIDIA GPU not installed")
            print("  - CUDA drivers not installed")
            print("  - PyTorch CPU-only version installed")
            
    except ImportError:
        print("❌ PyTorch not installed")
        return False
    
    # Check NVIDIA drivers
    print(f"\n🔧 System Information:")
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA drivers installed")
            # Extract GPU info from nvidia-smi
            lines = result.stdout.split('\n')
            for line in lines:
                if 'GeForce' in line or 'RTX' in line or 'GTX' in line or 'Quadro' in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ NVIDIA drivers not found or nvidia-smi not available")
    except FileNotFoundError:
        print("❌ nvidia-smi command not found")
    
    # Check CUDA installation
    try:
        cuda_version = torch.version.cuda
        if cuda_version:
            print(f"✅ CUDA version: {cuda_version}")
        else:
            print("❌ CUDA not available in PyTorch")
    except:
        print("❌ Could not determine CUDA version")
    
    # Check cuDNN
    try:
        cudnn_version = torch.backends.cudnn.version()
        print(f"✅ cuDNN version: {cudnn_version}")
        print(f"✅ cuDNN enabled: {torch.backends.cudnn.enabled}")
    except:
        print("❌ cuDNN not available")
    
    return cuda_available

def test_yolo_gpu():
    """Test YOLO model loading and GPU usage."""
    
    print(f"\n🧪 YOLO GPU Test")
    print("=" * 30)
    
    try:
        from ultralytics import YOLO
        import torch
        
        # Test with a small model first
        print("📦 Loading YOLOv8n (nano) for testing...")
        model = YOLO('yolov8n.pt')  # This will download if not present
        
        if torch.cuda.is_available():
            print("🚀 Moving model to GPU...")
            model.to('cuda:0')
            print("✅ Model successfully moved to GPU")
            
            # Test inference
            print("🔍 Testing GPU inference...")
            import numpy as np
            test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            
            results = model(test_image, device='cuda:0')
            print("✅ GPU inference test PASSED")
            
            # Check GPU memory usage
            memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
            memory_cached = torch.cuda.memory_reserved(0) / 1024**3
            print(f"📊 GPU Memory - Allocated: {memory_allocated:.2f}GB, Cached: {memory_cached:.2f}GB")
            
        else:
            print("❌ CUDA not available, testing CPU inference...")
            test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            results = model(test_image, device='cpu')
            print("✅ CPU inference test PASSED")
            
    except ImportError:
        print("❌ Ultralytics not installed")
        print("Install with: pip install ultralytics")
        return False
    except Exception as e:
        print(f"❌ YOLO test failed: {e}")
        return False
    
    return True

def provide_recommendations():
    """Provide recommendations based on diagnostic results."""
    
    print(f"\n💡 Recommendations")
    print("=" * 30)
    
    import torch
    
    if not torch.cuda.is_available():
        print("🔧 To enable GPU support:")
        print("1. Install NVIDIA GPU drivers")
        print("2. Install CUDA toolkit")
        print("3. Install PyTorch with CUDA support:")
        print("   pip uninstall torch torchvision")
        print("   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
        print("4. Restart your system")
        
    else:
        print("✅ GPU is available and working!")
        print("🚀 Your system is ready for GPU-accelerated inference")
        
        # Performance tips
        print(f"\n⚡ Performance Tips:")
        print("- Use batch processing for multiple images")
        print("- Consider mixed precision (FP16) for faster inference")
        print("- Monitor GPU memory usage to avoid OOM errors")
        print("- Use appropriate image sizes (640x640 is standard)")

def main():
    """Main diagnostic function."""
    
    print("🎮 GPU Diagnostic Tool for YOLO Inference")
    print("This tool will check your GPU setup and YOLO compatibility")
    print()
    
    # Run diagnostics
    gpu_available = check_gpu_availability()
    yolo_works = test_yolo_gpu()
    
    print(f"\n📋 Summary")
    print("=" * 20)
    print(f"GPU Available: {'✅ YES' if gpu_available else '❌ NO'}")
    print(f"YOLO GPU Ready: {'✅ YES' if yolo_works and gpu_available else '❌ NO'}")
    
    # Provide recommendations
    provide_recommendations()
    
    if gpu_available and yolo_works:
        print(f"\n🎉 Success! Your system is ready for GPU-accelerated YOLO inference!")
        print("You can now run the video inference server with GPU support.")
    else:
        print(f"\n⚠️  Issues detected. Please follow the recommendations above.")

if __name__ == "__main__":
    main()

