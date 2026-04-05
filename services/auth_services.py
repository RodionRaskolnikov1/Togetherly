from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from datetime import datetime

from utils.auth_utils import create_access_token
from utils.hash import hash_password, verify_password
from utils.logs import create_user_log

import crud.user as crud

from models import (
    Community, Profile, Invite, PasswordReset, User,
    UserImage, CurrentAddress
)

from utils.enums import AccountStatusEnum


def login_service(data, request, db : Session):
    identifier = data.identifier.strip()
    user = None
    if "@" in identifier:
        user = crud.get_user_by_email(db, identifier)
    else: 
        user = crud.get_user_by_phone(db, identifier)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    pending_invite = db.query(Invite).filter(
        Invite.user_id == user.id,
        Invite.used == False,
        Invite.expires_at > datetime.utcnow()
    ).first()
    
    if pending_invite:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated. Please set your password using the invite link."
        )


    if user.account_status == AccountStatusEnum.disabled:
        raise HTTPException(403, "Account is disabled")

    if not verify_password(data.password, str(user.password_hash)):
        create_user_log(
                db=db,
                user_id=user.id,
                action="LOGIN_FAILED",
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    
    token = create_access_token(user.id)
    
    create_user_log(
        db=db,
        user_id=user.id,
        action="USER_LOGIN",
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return {"access_token": token, "token_type": "bearer"}

        
def get_invite_details_service(token: str, db: Session):
    invite = db.query(Invite).filter(
        Invite.token == token,
        Invite.used == False
    ).first()

    if not invite:
        raise HTTPException(400, "Invalid or already used invite token")

    if invite.expires_at < datetime.utcnow():
        raise HTTPException(400, "Invite token has expired")

    user = db.query(User).filter_by(id=invite.user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    return {
        "email": user.email,
        "phone": user.phone,
        "first_name": user.first_name,
        "father_name": user.father_name,
        "last_name": user.last_name,
        "dob": user.dob,
        "gender": user.gender.value if hasattr(user.gender, "value") else user.gender,
    }
    
    
def setup_password_service(payload, db : Session):
    
    invite = db.query(Invite).filter(
        Invite.token == payload.token,
        Invite.used == False
    ).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used invite token"
        )

    if invite.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite token has expired"
        )
    
    user = db.query(User).filter_by(id=invite.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    try:        
        user.phone = payload.phone if payload.phone else None
        user.first_name = payload.first_name
        user.father_name = payload.father_name
        user.last_name = payload.last_name
        user.dob = payload.dob
        user.gender = payload.gender
        user.password_hash = hash_password(payload.password)
        invite.used = True
        
        db.commit()
    
        return {"message": "Password set successfully. You can now log in."}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(500, "Failed to set up account. Please try again.")

    
def password_reset_request_service(payload, db : Session):
    
    identifier = payload.identifier.strip()

    user = None
    if "@" in identifier:
        user = crud.get_user_by_email(db, identifier)
    else:
        user = crud.get_user_by_phone(db, identifier)

    if not user:
        return {"message": "If the account exists, a password reset link has been sent."}

    from utils.enums import RoleEnum
    if user.role not in [RoleEnum.community_admin.value, RoleEnum.coordinator.value]:
        return {"message": "Password reset is only available for invited community admins and coordinators."}

    db.query(PasswordReset).filter(
        PasswordReset.user_id == user.id,
        PasswordReset.used == False,
        PasswordReset.expires_at > datetime.utcnow()
    ).update({"used": True})

    import secrets
    from datetime import timedelta

    token = secrets.token_urlsafe(32)
    reset = PasswordReset(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(reset)
    db.commit()

    from utils.otp import send_password_reset_email
    send_password_reset_email(email=user.email, token=token)

    return {"message": "If the account exists, a password reset link has been sent."}


def password_reset_confirm_service(payload, db : Session):

    reset = db.query(PasswordReset).filter(
        PasswordReset.token == payload.token,
        PasswordReset.used == False
    ).first()

    if not reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used reset token"
        )

    if reset.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    user = db.query(User).filter_by(id=reset.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.password_hash = hash_password(payload.password)
    reset.used = True

    db.commit()

    return {"message": "Password reset successfully. You can now log in with your new password."}



def forgot_password_request_service(payload, db: Session):
    target = payload.email or payload.phone
    if not target:
        raise HTTPException(400, "Either email or phone is required")
 
    from utils.otp import is_user_blocked, send_otp
    from services.registration_service import detect_channel
 
    # look up user — always return same message to avoid account enumeration
    if payload.email:
        user = crud.get_user_by_email(db, payload.email)
    else:
        user = crud.get_user_by_phone(db, payload.phone)
 
    if not user:
        return {"message": "If an account exists for that contact, an OTP has been sent."}
 
    if user.account_status == AccountStatusEnum.disabled:
        return {"message": "If an account exists for that contact, an OTP has been sent."}
 
    is_user_blocked(target)
 
    via_email = detect_channel(target)
    send_otp(target, via_email=via_email)
 
    return {"message": "If an account exists for that contact, an OTP has been sent."}
 
 
def forgot_password_verify_service(payload, db: Session):
    target = payload.email or payload.phone
    if not target:
        raise HTTPException(400, "Either email or phone is required")
 
    from utils.otp import verify_otp
 
    if not verify_otp(target, payload.otp):
        raise HTTPException(400, "Invalid or expired OTP")
 
    if payload.email:
        user = crud.get_user_by_email(db, payload.email)
    else:
        user = crud.get_user_by_phone(db, payload.phone)
 
    if not user:
        raise HTTPException(404, "User not found")
 
    if user.account_status == AccountStatusEnum.disabled:
        raise HTTPException(403, "Account is disabled")
 
    user.password_hash = hash_password(payload.new_password)
 
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(500, "Failed to update password. Please try again.")
 
    return {"message": "Password reset successfully. You can now log in."}



def password_reset_service(payload, current_user, db : Session):
    
    user = db.query(User).filter_by(id=current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not verify_password(payload.old_password, str(user.password_hash)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect old password")
    
    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password reset successfully. You can now log in with your new password."}
    

    