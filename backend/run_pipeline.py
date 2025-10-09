#!/usr/bin/env python3
"""
Run the Parallel Image Processing Pipeline
This script starts the pipeline that monitors the violation folder
and processes images as they are saved.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Imagepipeline import ParallelImagePipeline

def main():
    """Main function to run the pipeline."""
    print("🚀 Starting Parallel Image Processing Pipeline...")
    print("📋 This pipeline will:")
    print("   • Monitor the 'violation' folder for new images")
    print("   • Enhance images for better clarity")
    print("   • Read number plates using Gemini AI")
    print("   • Save results to 'processed' and 'results' folders")
    print()
    
    # Create and start the pipeline
    pipeline = ParallelImagePipeline()
    
    try:
        pipeline.start()
        
        # Keep running
        print("🔄 Pipeline is running... Press Ctrl+C to stop")
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping pipeline...")
        pipeline.stop()
        print("👋 Pipeline stopped successfully!")

if __name__ == "__main__":
    main()
