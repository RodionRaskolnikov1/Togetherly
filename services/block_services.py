from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import BlockedUser, User
from utils.auth_utils import get_current_user_with_details

def block_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_details)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot block yourself")

    existing = db.query(BlockedUser).filter(
        BlockedUser.blocker_id == current_user.id,
        BlockedUser.blocked_id == user_id
    ).first()

    if existing:
        return {"message": "User already blocked"}

    block = BlockedUser(
        blocker_id=current_user.id,
        blocked_id=user_id
    )

    db.add(block)
    db.commit()

    return {"message": "User blocked successfully"}

def unblock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_details)
):
    block = db.query(BlockedUser).filter(
        BlockedUser.blocker_id == current_user.id,
        BlockedUser.blocked_id == user_id
    ).first()

    if not block:
        raise HTTPException(status_code=404, detail="User not blocked")

    db.delete(block)
    db.commit()

    return {"message": "User unblocked successfully"}

def my_blocked_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_details)
):
    blocked = db.query(User).join(
        BlockedUser,
        BlockedUser.blocked_id == User.id
    ).filter(
        BlockedUser.blocker_id == current_user.id
    ).all()

    return blocked
