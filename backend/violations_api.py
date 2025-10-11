from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost/safehead_violations')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# =============================
# DATABASE MODELS
# =============================
class Violation(db.Model):
    __tablename__ = 'violations'
    
    number_plate = db.Column(db.String(20), primary_key=True)
    violation_type = db.Column(db.String(50), nullable=False)
    violation_description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    image_public_id = db.Column(db.String(100))
    violation_timestamp = db.Column(db.DateTime, nullable=False)
    confidence_score = db.Column(db.Float)
    vehicle_id = db.Column(db.String(50))
    crop_filename = db.Column(db.String(200))
    location = db.Column(db.String(100))
    camera_id = db.Column(db.String(50))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'number_plate': self.number_plate,
            'violation_type': self.violation_type,
            'violation_description': self.violation_description,
            'image_url': self.image_url,
            'image_public_id': self.image_public_id,
            'violation_timestamp': self.violation_timestamp.isoformat() if self.violation_timestamp else None,
            'confidence_score': self.confidence_score,
            'vehicle_id': self.vehicle_id,
            'crop_filename': self.crop_filename,
            'location': self.location,
            'camera_id': self.camera_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_violation(cls, **kwargs):
        violation = cls(**kwargs)
        return violation

# =============================
# API ROUTES
# =============================

@app.route('/api/violations', methods=['POST'])
def create_violation():
    """Create a new violation record."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['number_plate', 'violation_type', 'violation_timestamp']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if violation already exists
        existing_violation = Violation.query.filter_by(number_plate=data['number_plate']).first()
        
        if existing_violation:
            # Update existing violation
            for key, value in data.items():
                if hasattr(existing_violation, key):
                    setattr(existing_violation, key, value)
            existing_violation.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Violation updated successfully',
                'violation': existing_violation.to_dict()
            }), 200
        else:
            # Create new violation
            violation = Violation.create_violation(**data)
            db.session.add(violation)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Violation created successfully',
                'violation': violation.to_dict()
            }), 201
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating violation: {str(e)}'
        }), 500

@app.route('/api/violations', methods=['GET'])
def get_violations():
    """Get all violations with pagination and filtering."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        
        # Build query
        query = Violation.query
        
        if status:
            query = query.filter(Violation.status == status)
        
        if search:
            query = query.filter(Violation.number_plate.ilike(f'%{search}%'))
        
        # Order by created_at descending
        query = query.order_by(Violation.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        violations = [violation.to_dict() for violation in pagination.items]
        
        return jsonify({
            'success': True,
            'violations': violations,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching violations: {str(e)}'
        }), 500

@app.route('/api/violations/<number_plate>', methods=['GET'])
def get_violation(number_plate):
    """Get a specific violation by number plate."""
    try:
        violation = Violation.query.filter_by(number_plate=number_plate).first()
        
        if not violation:
            return jsonify({
                'success': False,
                'message': 'Violation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'violation': violation.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching violation: {str(e)}'
        }), 500

@app.route('/api/violations/<number_plate>', methods=['PUT'])
def update_violation(number_plate):
    """Update a violation's status."""
    try:
        data = request.get_json()
        violation = Violation.query.filter_by(number_plate=number_plate).first()
        
        if not violation:
            return jsonify({
                'success': False,
                'message': 'Violation not found'
            }), 404
        
        # Update fields
        for key, value in data.items():
            if hasattr(violation, key):
                setattr(violation, key, value)
        
        violation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Violation updated successfully',
            'violation': violation.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating violation: {str(e)}'
        }), 500

@app.route('/api/violations/<number_plate>', methods=['DELETE'])
def delete_violation(number_plate):
    """Delete a violation and its associated image from Cloudinary."""
    try:
        violation = Violation.query.filter_by(number_plate=number_plate).first()
        
        if not violation:
            return jsonify({
                'success': False,
                'message': 'Violation not found'
            }), 404
        
        # Delete image from Cloudinary if it exists
        if violation.image_public_id:
            try:
                cloudinary.uploader.destroy(violation.image_public_id)
                print(f"✅ Deleted image from Cloudinary: {violation.image_public_id}")
            except Exception as e:
                print(f"⚠️ Error deleting image from Cloudinary: {e}")
        
        # Delete from database
        db.session.delete(violation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Violation deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting violation: {str(e)}'
        }), 500

@app.route('/api/violations/stats', methods=['GET'])
def get_violations_stats():
    """Get violation statistics."""
    try:
        total_violations = Violation.query.count()
        active_violations = Violation.query.filter_by(status='active').count()
        resolved_violations = Violation.query.filter_by(status='resolved').count()
        dismissed_violations = Violation.query.filter_by(status='dismissed').count()
        
        # Recent violations (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_violations_24h = Violation.query.filter(
            Violation.created_at >= yesterday
        ).count()
        
        # Violations by type
        violations_by_type = db.session.query(
            Violation.violation_type,
            db.func.count(Violation.violation_type)
        ).group_by(Violation.violation_type).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_violations': total_violations,
                'active_violations': active_violations,
                'resolved_violations': resolved_violations,
                'dismissed_violations': dismissed_violations,
                'recent_violations_24h': recent_violations_24h,
                'violations_by_type': dict(violations_by_type)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching stats: {str(e)}'
        }), 500

@app.route('/api/violations/export', methods=['GET'])
def export_violations():
    """Export all violations to CSV."""
    try:
        import csv
        import io
        
        violations = Violation.query.order_by(Violation.created_at.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Number Plate', 'Violation Type', 'Description', 'Timestamp',
            'Confidence Score', 'Vehicle ID', 'Location', 'Camera ID', 'Status',
            'Created At', 'Updated At'
        ])
        
        # Write data
        for violation in violations:
            writer.writerow([
                violation.number_plate,
                violation.violation_type,
                violation.violation_description,
                violation.violation_timestamp.isoformat() if violation.violation_timestamp else '',
                violation.confidence_score,
                violation.vehicle_id,
                violation.location,
                violation.camera_id,
                violation.status,
                violation.created_at.isoformat() if violation.created_at else '',
                violation.updated_at.isoformat() if violation.updated_at else ''
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=violations_export.csv'}
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error exporting violations: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'message': 'Violations API is running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# =============================
# DATABASE INITIALIZATION
# =============================
def init_db():
    """Initialize the database."""
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the app
    port = int(os.getenv('VIOLATIONS_API_PORT', 5001))
    print(f"🚀 Starting Violations API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
