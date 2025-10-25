from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Violation(db.Model):
    """Violation model for storing helmet violation records."""
    
    __tablename__ = 'violations'
    
    # Primary key - number plate
    number_plate = db.Column(db.String(20), primary_key=True, nullable=False)
    
    # Violation details
    violation_type = db.Column(db.String(50), nullable=False)  # e.g., 'no_helmet', 'helmet_violation'
    violation_description = db.Column(db.Text, nullable=True)
    
    # Image information
    image_url = db.Column(db.String(500), nullable=False)  # Cloudinary URL
    image_public_id = db.Column(db.String(200), nullable=True)  # Cloudinary public ID for deletion
    
    # Timing information
    violation_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Detection details
    confidence_score = db.Column(db.Float, nullable=True)  # Detection confidence
    vehicle_id = db.Column(db.String(50), nullable=True)  # Internal vehicle tracking ID
    crop_filename = db.Column(db.String(200), nullable=True)  # Original crop filename
    no_helmet_count = db.Column(db.Integer, nullable=True, default=1)  # Number of people without helmets
    
    # Location information (optional)
    location = db.Column(db.String(200), nullable=True)
    camera_id = db.Column(db.String(50), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, resolved, dismissed
    
    def __repr__(self):
        return f'<Violation {self.number_plate}: {self.violation_type}>'
    
    def to_dict(self):
        """Convert violation to dictionary for JSON serialization."""
        return {
            'number_plate': self.number_plate,
            'violation_type': self.violation_type,
            'violation_description': self.violation_description,
            'image_url': self.image_url,
            'image_public_id': self.image_public_id,
            'violation_timestamp': self.violation_timestamp.isoformat() if self.violation_timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'confidence_score': self.confidence_score,
            'vehicle_id': self.vehicle_id,
            'crop_filename': self.crop_filename,
            'no_helmet_count': self.no_helmet_count,
            'location': self.location,
            'camera_id': self.camera_id,
            'status': self.status
        }
    
    @classmethod
    def create_violation(cls, number_plate, violation_type, image_url, **kwargs):
        """Create a new violation record."""
        violation = cls(
            number_plate=number_plate,
            violation_type=violation_type,
            image_url=image_url,
            **kwargs
        )
        return violation
