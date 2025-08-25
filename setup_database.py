#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
from database.models import create_tables
from database.database_manager import DatabaseManager

def setup_database():
    """Setup database tables and test connection"""
    print("Setting up Housing Association Discovery Database...")
    
    # Load environment variables
    load_dotenv('config/api_keys.env')
    
    # Check if database URL is configured
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL found - using SQLite database")
        print("Database will be created as: housing_associations.db")
    else:
        print(f"Using configured database: {db_url}")
    
    try:
        # Create tables
        print("Creating database tables...")
        create_tables()
        
        # Test database connection
        print("Testing database connection...")
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        session.close()
        
        print("✅ Database setup complete!")
        if db_url:
            print(f"Connected to: {db_url}")
        else:
            print("Connected to: sqlite:///housing_associations.db")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        if db_url:
            print("\nTroubleshooting:")
            print("1. Ensure PostgreSQL is running")
            print("2. Check DATABASE_URL in config/api_keys.env")
            print("3. Verify database exists and user has permissions")
        else:
            print("\nTroubleshooting:")
            print("1. Ensure you have write permissions in this directory")
            print("2. Check if SQLite is properly installed")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)