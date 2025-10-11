#!/usr/bin/env python3
"""
Database initialization script for Safehead violation tracking system.
This script creates the database and tables if they don't exist.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import Config

def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Connect to PostgreSQL server (not to the specific database)
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{Config.DB_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f'CREATE DATABASE "{Config.DB_NAME}"')
            print(f"✅ Database '{Config.DB_NAME}' created successfully")
        else:
            print(f"✅ Database '{Config.DB_NAME}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def create_tables():
    """Create tables in the database."""
    try:
        from app import app, db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def test_connection():
    """Test database connection."""
    try:
        from app import app, db
        
        with app.app_context():
            # Test connection by executing a simple query
            result = db.session.execute(db.text("SELECT 1")).fetchone()
            if result:
                print("✅ Database connection test successful")
                return True
            else:
                print("❌ Database connection test failed")
                return False
                
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

def main():
    """Main initialization function."""
    print("🚀 Initializing Safehead violation database...")
    print(f"📊 Database: {Config.DB_NAME}")
    print(f"🏠 Host: {Config.DB_HOST}:{Config.DB_PORT}")
    print(f"👤 User: {Config.DB_USER}")
    print()
    
    # Check if required environment variables are set
    if not Config.CLOUDINARY_CLOUD_NAME:
        print("⚠️  Warning: CLOUDINARY_CLOUD_NAME not set. Image uploads will not work.")
    
    if not Config.CLOUDINARY_API_KEY:
        print("⚠️  Warning: CLOUDINARY_API_KEY not set. Image uploads will not work.")
    
    if not Config.CLOUDINARY_API_SECRET:
        print("⚠️  Warning: CLOUDINARY_API_SECRET not set. Image uploads will not work.")
    
    print()
    
    # Step 1: Create database
    if not create_database():
        print("❌ Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 2: Create tables
    if not create_tables():
        print("❌ Failed to create tables. Exiting.")
        sys.exit(1)
    
    # Step 3: Test connection
    if not test_connection():
        print("❌ Database connection test failed. Exiting.")
        sys.exit(1)
    
    print()
    print("🎉 Database initialization completed successfully!")
    print()
    print("📋 Next steps:")
    print("1. Set up your Cloudinary account and add credentials to .env file")
    print("2. Run the Flask application: python app.py")
    print("3. Access the API at http://localhost:5000")

if __name__ == "__main__":
    main()
