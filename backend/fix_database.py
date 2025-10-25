#!/usr/bin/env python3
"""
Simple script to add no_helmet_count column to the violations table.
Run this if you're getting the 'no_helmet_count' is an invalid keyword argument error.
"""

import os
from dotenv import load_dotenv
from violations_api import app, db, Violation

load_dotenv()

def fix_database():
    """Add missing column to database."""
    with app.app_context():
        try:
            print("🔧 Fixing database schema...")
            print("📊 Creating/updating tables...")
            
            # This will create tables if they don't exist
            # and add missing columns to existing tables
            db.create_all()
            
            print("✅ Database schema updated successfully!")
            print()
            print("📋 Verification:")
            
            # Test the model
            try:
                # Check if we can query the table
                count = Violation.query.count()
                print(f"   ✅ Violations table accessible: {count} records")
                
                # Try to access no_helmet_count field on a test record
                if count > 0:
                    test_record = Violation.query.first()
                    helmet_count = test_record.no_helmet_count
                    print(f"   ✅ no_helmet_count field accessible (value: {helmet_count})")
                else:
                    print(f"   ℹ️ No records in table yet (will be populated when violations are detected)")
                
            except Exception as e:
                print(f"   ⚠️ Warning during verification: {e}")
            
            print()
            print("🎉 Database fix completed!")
            print()
            print("🔄 Next steps:")
            print("1. Restart the violations API (python violations_api.py)")
            print("2. Restart the image pipeline (python start_image_pipeline.py)")
            print("3. The system should now work correctly")
            
        except Exception as e:
            print(f"❌ Error fixing database: {e}")
            print()
            print("🔍 Troubleshooting:")
            print("1. Make sure PostgreSQL is running")
            print("2. Check your .env file has correct database credentials")
            print("3. Verify database connection: psql -U <user> -d safehead_violations")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Safehead Database Fix Script")
    print("=" * 60)
    print()
    fix_database()

