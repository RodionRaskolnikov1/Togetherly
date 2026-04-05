from fastapi import APIRouter, Depends, Request
from database import get_db
from sqlalchemy.orm import Session

from services.super_admin_services import (
    add_communnity, fetch_communities, add_community_admin, 
    resend_invite_service, get_dashboard_details
)

from schemas.communitySchema import CommunityCreate
from schemas.community_admin_complete import CommunityAdminComplete

from utils.auth_utils import require_super_admin

router = APIRouter(prefix="/super-admin", tags=["super-admin"])


@router.get("/dashboard")
def dashboard(
        db: Session = Depends(get_db),
        current_user=Depends(require_super_admin)
    ):
    return get_dashboard_details(db, current_user)

@router.post("/register-community")
def register_community(
        payload: CommunityCreate, 
        db: Session = Depends(get_db),
        current_user=Depends(require_super_admin),
        request: Request = None
    ):
    return add_communnity(payload, db, current_user, request)

@router.post("/register-communityadmin")
def register_coordinator_admin(
        payload: CommunityAdminComplete, 
        db: Session = Depends(get_db),
        current_user=Depends(require_super_admin),
        request: Request = None
    ):
    return add_community_admin(payload, db, current_user, request)

@router.post("/resend-community-admin-invite")
def resend_invite(
        email: str, 
        db: Session = Depends(get_db),
        current_user=Depends(require_super_admin),
        request: Request = None
    ):
    return resend_invite_service(email, db, current_user, request)

@router.get("/fetch-communities")
def fetchall_communities(
        db: Session = Depends(get_db), 
        current_user=Depends(require_super_admin),
        request: Request = None
    ):
    return fetch_communities(db, current_user, request)