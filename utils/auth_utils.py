import os
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session, joinedload

import crud.user as crud

from models import (
    City, State, User, Coordinator, Profile, ProfileCommunity
)

from utils.enums import RoleEnum    

from database import get_db
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=(expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"exp": expire, "sub": subject}
    return jwt.encode(to_encode, SECRET_KEY, ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

def require_super_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    sub = payload.get("sub")
    
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = crud.get_user_by_id(db, sub)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    if user.role != RoleEnum.super_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return user
    
def require_community_coordinator(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    sub = payload.get("sub")
    
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = crud.get_user_by_id(db, sub)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    if user.role != RoleEnum.coordinator:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    coordinator = db.query(Coordinator).filter(
        Coordinator.user_id == user.id,
        Coordinator.is_active == True
    ).first()

    if not coordinator:
        raise HTTPException(403, "Coordinator is inactive or unauthorized")
    
    return user

def require_community_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    sub = payload.get("sub")
    
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = crud.get_user_by_id(db, sub)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    if user.role != RoleEnum.community_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    return user    
    
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


def get_user_with_details(user_id: str, db: Session):
    
    user = (
        db.query(User)
            .options(
                joinedload(User.profile).joinedload(Profile.education_details),
                joinedload(User.profile).joinedload(Profile.profession_details),
                joinedload(User.profile).joinedload(Profile.lifestyle),
                joinedload(User.profile).joinedload(Profile.current_address),
                joinedload(User.profile).joinedload(Profile.permanent_address),
                joinedload(User.profile).joinedload(Profile.horoscope),
                joinedload(User.profile).joinedload(Profile.family_details),
                joinedload(User.profile).joinedload(Profile.communities).joinedload(ProfileCommunity.community),
                joinedload(User.profile).joinedload(Profile.profile_images),
                joinedload(User.profile).joinedload(Profile.verification_documents),
            )
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
    
def get_current_user_with_details(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    uid = payload.get("sub")
    
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")

    return get_user_with_details(uid, db)
    


def validate_location(city_id, state_id, country_id, db: Session):
    
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
            raise HTTPException(status_code=400, detail="Invalid city_id")
        
    if city.state_id != state_id:
        raise HTTPException(status_code=400, detail="City does not belong to selected state")        
        
    state = db.query(State).filter(State.id == state_id).first()
    
    if not state:
        raise HTTPException(status_code=400, detail="Invalid state_id")
        
    if state.country_id != country_id:
        raise HTTPException(status_code=400, detail="State does not belong to selected country")
        