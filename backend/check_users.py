#!/usr/bin/env python3
"""
Script to check what users exist in the database and their details.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import get_db, engine
from src.models.user import User
from sqlalchemy.orm import Session


def check_users():
    """Check what users exist in the database."""
    
    # Create database session
    db = Session(engine)
    
    try:
        # Get all users
        users = db.query(User).all()
        
        if not users:
            print("❌ No users found in database")
            return
        
        print(f"✅ Found {len(users)} user(s) in database:")
        print("-" * 60)
        
        for user in users:
            print(f"📧 Email: {user.email}")
            print(f"👤 Name: {user.first_name} {user.last_name}")
            print(f"🆔 ID: {user.id}")
            print(f"🔒 Active: {user.is_active}")
            print(f"📅 Created: {user.created_at}")
            print(f"🔑 Password Hash: {user.password_hash[:50]}...")
            print("-" * 60)
        
    except Exception as e:
        print(f"❌ Error checking users: {e}")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("🔍 Checking users in database...")
    check_users()
    print("✅ Done!")