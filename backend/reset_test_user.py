#!/usr/bin/env python3
"""
Script to reset the test user password to a known value.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.auth import get_password_hash
from src.database import get_db, engine
from src.models.user import User
from sqlalchemy.orm import Session


def reset_test_user():
    """Reset the test user password to a known value."""
    
    # Create database session
    db = Session(engine)
    
    try:
        # Find the test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            print("❌ Test user not found: test@example.com")
            return
        
        # Reset password to "testpass123" (9+ characters to meet validation)
        new_password = "testpass123"
        hashed_password = get_password_hash(new_password)
        
        test_user.password_hash = hashed_password
        db.commit()
        
        print("✅ Test user password reset successfully!")
        print(f"   Email: test@example.com")
        print(f"   New Password: {new_password}")
        print(f"   User ID: {test_user.id}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error resetting test user password: {e}")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Resetting test user password...")
    reset_test_user()
    print("✅ Done!")