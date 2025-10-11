import cloudinary
import cloudinary.uploader
import cloudinary.api
from config import Config
import os
import base64
import time
from io import BytesIO
from PIL import Image

class CloudinaryService:
    """Service class for handling Cloudinary operations."""
    
    def __init__(self):
        """Initialize Cloudinary with configuration."""
        cloudinary.config(
            cloud_name=Config.CLOUDINARY_CLOUD_NAME,
            api_key=Config.CLOUDINARY_API_KEY,
            api_secret=Config.CLOUDINARY_API_SECRET
        )
    
    def upload_image_from_file(self, file_path, folder="violations", public_id=None):
        """
        Upload an image file to Cloudinary.
        
        Args:
            file_path (str): Path to the image file
            folder (str): Cloudinary folder to upload to
            public_id (str): Custom public ID for the image
            
        Returns:
            dict: Upload result with URL and public_id
        """
        try:
            # Generate public_id if not provided
            if not public_id:
                filename = os.path.basename(file_path)
                name, ext = os.path.splitext(filename)
                public_id = f"{folder}/{name}_{int(time.time())}"
            
            # Upload the image
            result = cloudinary.uploader.upload(
                file_path,
                folder=folder,
                public_id=public_id,
                resource_type="image",
                quality="auto",
                fetch_format="auto"
            )
            
            return {
                'success': True,
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'format': result['format'],
                'bytes': result['bytes']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_image_from_cv2(self, cv2_image, folder="violations", public_id=None):
        """
        Upload a CV2 image (numpy array) to Cloudinary.
        
        Args:
            cv2_image (numpy.ndarray): CV2 image array
            folder (str): Cloudinary folder to upload to
            public_id (str): Custom public ID for the image
            
        Returns:
            dict: Upload result with URL and public_id
        """
        try:
            import cv2
            import time
            
            # Generate public_id if not provided
            if not public_id:
                public_id = f"{folder}/violation_{int(time.time())}"
            
            # Convert CV2 image to PIL Image
            cv2_image_rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(cv2_image_rgb)
            
            # Convert PIL image to bytes
            img_buffer = BytesIO()
            pil_image.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)
            
            # Upload the image
            result = cloudinary.uploader.upload(
                img_buffer,
                folder=folder,
                public_id=public_id,
                resource_type="image",
                quality="auto",
                fetch_format="auto"
            )
            
            return {
                'success': True,
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'format': result['format'],
                'bytes': result['bytes']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_image_from_base64(self, base64_string, folder="violations", public_id=None):
        """
        Upload a base64 encoded image to Cloudinary.
        
        Args:
            base64_string (str): Base64 encoded image string
            folder (str): Cloudinary folder to upload to
            public_id (str): Custom public ID for the image
            
        Returns:
            dict: Upload result with URL and public_id
        """
        try:
            import time
            
            # Generate public_id if not provided
            if not public_id:
                public_id = f"{folder}/violation_{int(time.time())}"
            
            # Upload the image
            result = cloudinary.uploader.upload(
                base64_string,
                folder=folder,
                public_id=public_id,
                resource_type="image",
                quality="auto",
                fetch_format="auto"
            )
            
            return {
                'success': True,
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'format': result['format'],
                'bytes': result['bytes']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_image(self, public_id):
        """
        Delete an image from Cloudinary.
        
        Args:
            public_id (str): Public ID of the image to delete
            
        Returns:
            dict: Deletion result
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_image_info(self, public_id):
        """
        Get information about an image.
        
        Args:
            public_id (str): Public ID of the image
            
        Returns:
            dict: Image information
        """
        try:
            result = cloudinary.api.resource(public_id)
            return {
                'success': True,
                'info': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global instance
cloudinary_service = CloudinaryService()
