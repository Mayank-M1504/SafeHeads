#!/usr/bin/env python3
"""
Interactive .env file creator for Safehead.
This script helps you create a .env file with the correct configuration.
"""

import os

def create_env_file():
    """Create .env file interactively."""
    print("🔧 Safehead Environment Setup")
    print("=" * 40)
    print("This script will help you create a .env file with the correct configuration.")
    print()
    
    # Check if .env already exists
    if os.path.exists('.env'):
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ").lower()
        if response != 'y':
            print("❌ Setup cancelled")
            return
    
    print("Please provide the following information:")
    print()
    
    # Database configuration
    print("📊 Database Configuration:")
    db_username = input("PostgreSQL username (default: postgres): ").strip() or "postgres"
    db_password = input("PostgreSQL password: ").strip()
    db_host = input("PostgreSQL host (default: localhost): ").strip() or "localhost"
    db_port = input("PostgreSQL port (default: 5432): ").strip() or "5432"
    db_name = input("Database name (default: safehead_violations): ").strip() or "safehead_violations"
    
    print()
    print("☁️  Cloudinary Configuration:")
    cloud_name = input("Cloudinary cloud name: ").strip()
    cloud_api_key = input("Cloudinary API key: ").strip()
    cloud_api_secret = input("Cloudinary API secret: ").strip()
    
    print()
    print("🤖 Gemini AI Configuration:")
    gemini_api_key = input("Gemini API key: ").strip()
    
    print()
    print("🔧 Other Configuration:")
    secret_key = input("Flask secret key (default: auto-generated): ").strip()
    if not secret_key:
        import secrets
        secret_key = secrets.token_hex(32)
    
    location = input("Default location (default: Traffic Intersection 1): ").strip() or "Traffic Intersection 1"
    camera_id = input("Default camera ID (default: CAM001): ").strip() or "CAM001"
    
    # Create .env content
    env_content = f"""# Database Configuration
DATABASE_URL=postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME={cloud_name}
CLOUDINARY_API_KEY={cloud_api_key}
CLOUDINARY_API_SECRET={cloud_api_secret}

# Gemini AI Configuration
GEMINI_API_KEY={gemini_api_key}

# Violations API Configuration
VIOLATIONS_API_URL=http://localhost:5001
VIOLATIONS_API_PORT=5001

# Flask Configuration
SECRET_KEY={secret_key}

# Optional: Location and Camera Information
DEFAULT_LOCATION={location}
DEFAULT_CAMERA_ID={camera_id}
"""
    
    # Write .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print()
        print("✅ .env file created successfully!")
        print()
        print("Next steps:")
        print("1. Test database connection: python setup_database.py")
        print("2. Start the services: python start_all_services.py")
        print()
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    create_env_file()
