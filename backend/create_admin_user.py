#!/usr/bin/env python3
"""
Script to add an admin user to the database.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.auth import get_password_hash
from src.database import get_db, engine
from src.models.user import User
from sqlalchemy.orm import Session


def add_admin_user():
    """Add an admin user to the database."""

    # Create database session
    db = Session(engine)

    try:
        # Check if admin user already exists
        existing_user = db.query(User).filter(User.email == "admin@example.com").first()
        if existing_user:
            # Update role to ADMIN if not already
            if existing_user.role != "ADMIN":
                existing_user.role = "ADMIN"
                db.commit()
                print(f"✅ Updated existing user to admin: admin@example.com")
            else:
                print("✅ Admin user already exists: admin@example.com")
            print(f"   User ID: {existing_user.id}")
            print(f"   Role: {existing_user.role}")
            return

        # Create admin user
        hashed_password = get_password_hash("admin123")

        admin_user = User(
            email="admin@example.com",
            password_hash=hashed_password,
            first_name="Admin",
            last_name="User",
            role="ADMIN"
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ Admin user created successfully!")
        print(f"   Email: admin@example.com")
        print(f"   Password: admin123")
        print(f"   User ID: {admin_user.id}")
        print(f"   Name: {admin_user.first_name} {admin_user.last_name}")
        print(f"   Role: {admin_user.role}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Adding admin user to database...")
    add_admin_user()
    print("✅ Done!")