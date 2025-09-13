#!/usr/bin/env python3
"""
Script to add a test user to the database for development/testing purposes.
"""

import sys
import asyncio
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.auth import get_password_hash
from src.database import get_db, engine
from src.models.user import User
from sqlalchemy.orm import Session


def add_test_user():
    """Add a test user to the database."""
    
    # Create database session
    db = Session(engine)
    
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            print("✅ Test user already exists: test@example.com")
            print(f"   User ID: {existing_user.id}")
            return
        
        # Create test user with 8+ character password
        hashed_password = get_password_hash("testpass")
        
        test_user = User(
            email="test@example.com",
            password_hash=hashed_password,
            first_name="Test",
            last_name="User"
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print("✅ Test user created successfully!")
        print(f"   Email: test@example.com")
        print(f"   Password: testpass")
        print(f"   User ID: {test_user.id}")
        print(f"   Name: {test_user.first_name} {test_user.last_name}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test user: {e}")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Adding test user to database...")
    add_test_user()
    print("✅ Done!")