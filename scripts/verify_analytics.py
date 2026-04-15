import sys
import os
import sqlite3
from sqlalchemy import create_client_static
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Add backend dir to path
sys.path.append(r'D:\haronex\backend\matrimonialcommunity')

from database import engine, SessionLocal, Base
from models import User, UserLogs
from utils.enums import GenderEnum, RoleEnum, AccountStatusEnum
from utils.hash import hash_password

def setup_mock_data():
    db = SessionLocal()
    try:
        # Create a test user if not exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                password_hash=hash_password("password123"),
                first_name="Test",
                last_name="User",
                gender=GenderEnum.male,
                role=RoleEnum.user,
                account_status=AccountStatusEnum.active
            )
            db.add(test_user)
            db.flush()
        
        # Create some logs
        log = UserLogs(
            user_id=test_user.id,
            action="TEST_ACTION",
            ip_address="127.0.0.1",
            user_agent="TestAgent"
        )
        db.add(log)
        db.commit()
        print(f"Mock data created for user: {test_user.id}")
    except Exception as e:
        db.rollback()
        print(f"Error creating mock data: {e}")
    finally:
        db.close()

def verify_tables():
    # Check if tables exist
    inspector = sqlite3.connect('test.db')
    cursor = inspector.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:", [t[0] for t in tables])
    inspector.close()

if __name__ == "__main__":
    verify_tables()
    setup_mock_data()
    print("Verification complete.")
