#!/usr/bin/env python3
"""
Database migration script to add no_helmet_count column to violations table.
This script safely adds the new column to existing databases.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import Config

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in the table."""
    try:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"❌ Error checking column existence: {e}")
        return False

def add_no_helmet_count_column():
    """Add the no_helmet_count column to the violations table."""
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🔍 Checking if violations table exists...")
        
        # Check if violations table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'violations'
        """)
        
        if not cursor.fetchone():
            print("❌ Violations table does not exist. Please run init_db.py first.")
            return False
        
        print("✅ Violations table found")
        
        # Check if no_helmet_count column already exists
        print("🔍 Checking if no_helmet_count column exists...")
        
        if check_column_exists(cursor, 'violations', 'no_helmet_count'):
            print("✅ no_helmet_count column already exists. Migration not needed.")
            return True
        
        print("📝 Adding no_helmet_count column...")
        
        # Add the new column
        cursor.execute("""
            ALTER TABLE violations 
            ADD COLUMN no_helmet_count INTEGER DEFAULT 1
        """)
        
        print("✅ no_helmet_count column added successfully")
        
        # Update existing records to have a default value of 1
        print("🔄 Updating existing records with default no_helmet_count value...")
        
        cursor.execute("""
            UPDATE violations 
            SET no_helmet_count = 1 
            WHERE no_helmet_count IS NULL
        """)
        
        updated_rows = cursor.rowcount
        print(f"✅ Updated {updated_rows} existing records")
        
        # Add a comment to the column for documentation
        cursor.execute("""
            COMMENT ON COLUMN violations.no_helmet_count 
            IS 'Number of people detected without helmets in the violation'
        """)
        
        print("✅ Column documentation added")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding no_helmet_count column: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful."""
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = conn.cursor()
        
        print("🔍 Verifying migration...")
        
        # Check if the column exists and has the right properties
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'violations' AND column_name = 'no_helmet_count'
        """)
        
        result = cursor.fetchone()
        if result:
            column_name, data_type, is_nullable, column_default = result
            print(f"✅ Column verification successful:")
            print(f"   📊 Column: {column_name}")
            print(f"   🔢 Data Type: {data_type}")
            print(f"   🔓 Nullable: {is_nullable}")
            print(f"   🎯 Default: {column_default}")
        else:
            print("❌ Column verification failed - column not found")
            return False
        
        # Check existing data
        cursor.execute("SELECT COUNT(*) FROM violations")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM violations WHERE no_helmet_count IS NOT NULL")
        records_with_count = cursor.fetchone()[0]
        
        print(f"📊 Database statistics:")
        print(f"   📋 Total violations: {total_records}")
        print(f"   🚫 Records with no_helmet_count: {records_with_count}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False

def main():
    """Main migration function."""
    print("🚀 Safehead Database Migration: Adding no_helmet_count Column")
    print("=" * 60)
    print(f"📊 Database: {Config.DB_NAME}")
    print(f"🏠 Host: {Config.DB_HOST}:{Config.DB_PORT}")
    print(f"👤 User: {Config.DB_USER}")
    print()
    
    # Step 1: Add the column
    print("📝 Step 1: Adding no_helmet_count column...")
    if not add_no_helmet_count_column():
        print("❌ Migration failed. Exiting.")
        sys.exit(1)
    
    print()
    
    # Step 2: Verify the migration
    print("🔍 Step 2: Verifying migration...")
    if not verify_migration():
        print("❌ Migration verification failed. Exiting.")
        sys.exit(1)
    
    print()
    print("🎉 Migration completed successfully!")
    print()
    print("📋 What was added:")
    print("   ✅ no_helmet_count column (INTEGER, DEFAULT 1)")
    print("   ✅ Updated existing records with default value")
    print("   ✅ Added column documentation")
    print()
    print("🔄 Next steps:")
    print("1. Restart your Flask application to use the new field")
    print("2. The ImagePipeline will now include no_helmet_count in violation data")
    print("3. API responses will include the no_helmet_count field")

if __name__ == "__main__":
    main()

