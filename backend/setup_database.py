#!/usr/bin/env python3
"""
Database setup script for Safehead Violations API.
This script helps you set up the PostgreSQL database and test the connection.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

def test_connection(host, port, database, user, password):
    """Test PostgreSQL connection."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.close()
        return True, "Connection successful!"
    except Exception as e:
        return False, str(e)

def create_database(host, port, user, password, db_name):
    """Create the database if it doesn't exist."""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database='postgres',
            user=user,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        
        if cursor.fetchone():
            print(f"✅ Database '{db_name}' already exists")
        else:
            # Create database
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name)
            ))
            print(f"✅ Database '{db_name}' created successfully")
        
        cursor.close()
        conn.close()
        return True, "Database setup complete"
        
    except Exception as e:
        return False, str(e)

def main():
    """Main setup function."""
    print("🔧 Safehead Database Setup")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Get database configuration
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("\n📝 Please create a .env file with the following content:")
        print("DATABASE_URL=postgresql://username:password@localhost:5432/safehead_violations")
        print("\nReplace 'username' and 'password' with your PostgreSQL credentials")
        return
    
    # Parse DATABASE_URL
    try:
        # Format: postgresql://username:password@host:port/database
        parts = db_url.replace('postgresql://', '').split('@')
        if len(parts) != 2:
            raise ValueError("Invalid DATABASE_URL format")
        
        user_pass = parts[0].split(':')
        if len(user_pass) != 2:
            raise ValueError("Invalid username:password format")
        
        user, password = user_pass
        host_port_db = parts[1].split('/')
        if len(host_port_db) != 2:
            raise ValueError("Invalid host:port/database format")
        
        host_port = host_port_db[0].split(':')
        if len(host_port) != 2:
            raise ValueError("Invalid host:port format")
        
        host, port = host_port
        database = host_port_db[1]
        
        print(f"📊 Host: {host}")
        print(f"🔌 Port: {port}")
        print(f"👤 User: {user}")
        print(f"🗄️  Database: {database}")
        print()
        
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        print("Expected format: postgresql://username:password@localhost:5432/safehead_violations")
        return
    
    # Test connection to postgres database first
    print("🔍 Testing connection to PostgreSQL...")
    success, message = test_connection(host, port, 'postgres', user, password)
    
    if not success:
        print(f"❌ Connection failed: {message}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your username and password")
        print("3. Verify the host and port are correct")
        print("4. Ensure PostgreSQL allows connections from localhost")
        return
    
    print(f"✅ {message}")
    
    # Create the database
    print(f"\n🗄️  Creating database '{database}'...")
    success, message = create_database(host, port, user, password, database)
    
    if not success:
        print(f"❌ Database creation failed: {message}")
        return
    
    print(f"✅ {message}")
    
    # Test connection to the new database
    print(f"\n🔍 Testing connection to '{database}'...")
    success, message = test_connection(host, port, database, user, password)
    
    if not success:
        print(f"❌ Connection to new database failed: {message}")
        return
    
    print(f"✅ {message}")
    
    print("\n🎉 Database setup complete!")
    print("You can now run the Violations API:")
    print("python backend/violations_api.py")

if __name__ == "__main__":
    main()
