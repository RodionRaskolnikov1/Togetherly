from fastapi import HTTPException
from sqlalchemy.orm import Session

from utils.otp import (
    send_otp,
    verify_otp,
    check_cooldown,
    is_user_blocked
)
from utils.logs import create_user_log
from services.registration_service import detect_channel

def send_verification_email_service(current_user, db):
    if not current_user.email:
        raise HTTPException(status_code=400, detail="No email")
    if current_user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    send_otp(current_user.email, via_email=True)
    return {"message": "OTP sent"}


def send_verification_phone_service(current_user, db):
    if not current_user.phone:
        raise HTTPException(status_code=400, detail="No phone")
    if current_user.phone_verified:
        raise HTTPException(status_code=400, detail="Phone already verified")
    send_otp(current_user.phone, via_email=False)
    return {"message": "OTP sent"}


def verify_secondary_email_service(current_user, otp, db):
    if not current_user.email:
        raise HTTPException(status_code=400, detail="No email")
    if current_user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    if not verify_otp(current_user.email, otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    current_user.email_verified = True
    current_user.account_status = "email_verified" if not current_user.phone_verified else "active"
    db.commit()
    
    create_user_log(
        db=db,
        user_id=current_user.id,
        action="EMAIL_VERIFIED"
    )

    return {"message": "Email verified"}


def verify_secondary_phone_service(current_user, otp, db):
    if not current_user.phone:
        raise HTTPException(status_code=400, detail="No phone")
    if current_user.phone_verified:
        raise HTTPException(status_code=400, detail="Phone already verified")
    if not verify_otp(current_user.phone, otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    current_user.phone_verified = True
    current_user.account_status = "phone_verified" if not current_user.email_verified else "active"
    db.commit()
    
    create_user_log(
        db=db,
        user_id=current_user.id,
        action="PHONE_VERIFIED"
    )

    return {"message": "Phone verified"}

def resend_otp_service(target: str, db: Session):

    if not target:
        raise HTTPException(status_code=400, detail="Target required")
    
    is_user_blocked(target)   
    check_cooldown(target)
    
    via_email = detect_channel(target)
    send_otp(target, via_email=via_email)
    return {"message": "OTP resent successfully"}

