from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import BlockedUser, User
from services.block_services import my_blocked_users, block_user, unblock_user
from utils.auth_utils import get_current_user_with_details

router = APIRouter(prefix="/block", tags=["Block"])

@router.post("/{user_id}")
def block(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_details)
):
    return block_user(user_id, db, current_user)

@router.delete("/{user_id}")
def unblock(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_details)
):
    return unblock_user(user_id, db, current_user)

@router.get("/me")
def blocked_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_details)
):
    return my_blocked_users(db,current_user)
