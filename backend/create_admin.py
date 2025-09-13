#!/usr/bin/env python3
"""
Create admin user for testing authentication
"""
import sys
sys.path.append('src')

from database import SessionLocal
from models.user import User
from core.auth import get_password_hash
import uuid

def main():
    db = SessionLocal()
    try:
        # Check if admin user exists
        user = db.query(User).filter(User.email == 'admin@example.com').first()
        if user:
            print('Admin user already exists')
            return

        # Create admin user
        user = User(
            id=uuid.uuid4(),
            email='admin@example.com',
            password_hash=get_password_hash('admin123'),
            first_name='Admin',
            last_name='User',
            is_active=True,
            role='admin'
        )
        db.add(user)
        db.commit()
        print('Admin user created successfully')
        print(f'Email: admin@example.com')
        print(f'Password: admin123')

    except Exception as e:
        print(f'Error creating admin user: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    main()