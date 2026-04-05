from sqlalchemy.orm import Session
from models import User
from schemas.userSchema import UserRegister

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_phone(db: Session, phone: str):
    return db.query(User).filter(User.phone == phone).first()

def get_user_by_id(db: Session, id: str):
    return db.query(User).filter(User.id == id).first()

def create_user(db: Session, user: UserRegister, password_hash: str):
    db_user = User(
        email=user.email,
        phone=user.phone,
        password_hash=password_hash,
        first_name=user.first_name,
        last_name=user.last_name,
        dob=user.dob,
        gender=user.gender
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


