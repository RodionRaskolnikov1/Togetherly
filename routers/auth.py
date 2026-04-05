from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db

from schemas.userSchema import (
    Login, Token, 
    SetupPassword, PasswordResetRequest,
    PasswordResetConfirm, PasswordResetUser
)
from schemas.dashboardSchema import DashboardResponse
from schemas.userSchema import ForgotPasswordRequest, ForgotPasswordVerify


from utils.auth_utils import (
    get_current_user_with_details, 
    get_current_user
)

from services.auth_services import (
    login_service, setup_password_service, 
    password_reset_request_service, password_reset_confirm_service,
    get_invite_details_service, password_reset_service,
    forgot_password_request_service, forgot_password_verify_service
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(data: Login, request: Request, db: Session = Depends(get_db)):
    return login_service(data, request, db)

    

@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "role": current_user.role,
        "email": current_user.email,
        "phone": current_user.phone
    }


@router.get("/dashboard", response_model=DashboardResponse, response_model_exclude_none=True)
def me(current_user=Depends(get_current_user_with_details)):
    return current_user
 

@router.get("/invite-details")
def get_invite_details(token: str, db: Session = Depends(get_db)):
    return get_invite_details_service(token, db)    


@router.post("/setup-password")
def setup_password(
        payload : SetupPassword, 
        db : Session = Depends(get_db)
    ):
    return setup_password_service(payload, db)
    


@router.post("/password-reset-request")
def password_reset_request(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    return password_reset_request_service(payload, db)


@router.post("/password-reset-confirm")
def password_reset_confirm(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    return password_reset_confirm_service(payload, db)


@router.post("/password-reset")
def password_reset(
        payload: PasswordResetUser, 
        current_user = Depends(get_current_user),
        db : Session = Depends(get_db)
    ):
    return password_reset_service(payload, current_user, db)



@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return forgot_password_request_service(payload, db)
 
 
@router.post("/forgot-password/verify")
def forgot_password_verify(payload: ForgotPasswordVerify, db: Session = Depends(get_db)):
    return forgot_password_verify_service(payload, db)


