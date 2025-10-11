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
    # Create and start the pipeline
    pipeline = ParallelImagePipeline()
    
    try:
        pipeline.start()
        
        # Keep running
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        pipeline.stop()

if __name__ == "__main__":
    main()
