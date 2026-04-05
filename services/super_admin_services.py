from datetime import datetime, timedelta
from sqlalchemy import func
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    Community, CommunityAdmin, User, Invite, SuperAdminLogs
)

from utils.enums import RoleEnum
from utils.hash import hash_password
from utils.otp import send_admin_invite_email
from utils.logs import create_super_admin_log
import secrets

def add_communnity(payload, db: Session, current_user : User, request):
    
    
    exist = db.query(Community).filter(
        Community.city_id == payload.city_id,
        Community.religion_id == payload.religion_id,
        Community.caste_id == payload.caste_id, 
        Community.sub_caste_id == payload.sub_caste_id
    ).first()
    
    if exist:
        raise HTTPException(
            status_code=400,
            detail="Community Exist"
        )
        
    community = Community(
        city_id=payload.city_id,
        religion_id=payload.religion_id,
        caste_id=payload.caste_id,
        sub_caste_id=payload.sub_caste_id,
        description=payload.description,
        display_name=payload.display_name
    )

    db.add(community)
    db.commit()
    db.refresh(community)
    
    create_super_admin_log(
        db = db,
        super_admin_id = current_user.id,
        action= f"ADD_COMMUNITY: {community.display_name}",
        ip = request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {
        "id": community.id,
        "display_name": community.display_name
    }
    
    
def add_community_admin(payload, db: Session, current_user : User, request):

    community = db.query(Community).filter_by(id=payload.community_id).first()
    if not community:
        raise HTTPException(400, "Invalid community")

    existing_admin = db.query(CommunityAdmin).filter_by(
        community_id=payload.community_id
    ).first()

    if existing_admin:
        raise HTTPException(400, "Community already has an admin")


    email = payload.user.email
    phone = payload.user.phone

    query = db.query(User)

    if email and phone:
        query = query.filter((User.email == email) | (User.phone == phone))
    elif email:
        query = query.filter(User.email == email)
    elif phone:
        query = query.filter(User.phone == phone)

    existing_user = query.first()

    if existing_user:
        raise HTTPException(400, "User already exists")
    
    internal_password = secrets.token_urlsafe(32)
    
    try:
        user = User(
            email=payload.user.email,
            phone=payload.user.phone,
            password_hash=hash_password(internal_password),
            first_name=payload.user.first_name,
            father_name=payload.user.father_name,
            last_name=payload.user.last_name,
            dob=payload.user.dob,
            gender=payload.user.gender.value,
            role=RoleEnum.community_admin.value
        )
        db.add(user)
        db.flush()  

        admin = CommunityAdmin( 
            user_id=user.id,    
            community_id=payload.community_id
        )
        db.add(admin)
        
        token = secrets.token_urlsafe(32)
        
        invite = Invite(
            user_id=user.id,
            token=token,
            role=user.role,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(invite)
        
        db.commit()
        db.refresh(admin)
        
        send_admin_invite_email(email = payload.user.email, token =  token)
        
        create_super_admin_log(
            db = db,
            super_admin_id = current_user.id,
            action= f"Assigned community admin: {user.first_name} {user.last_name} to community: {community.display_name}",
            ip = request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return {
            "admin_id": admin.id,
            "user_id": user.id,
            "community_id": community.id,
            "status": "INVITE_SENT"
        }   
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

def resend_invite_service(email : str, db : Session, current_user : User, request):

    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(404, "User not found")

    if (user.role != RoleEnum.community_admin.value):
        raise HTTPException(400, "User is not a community admin")
    
    
    db.query(Invite).filter(
        Invite.user_id == user.id,
        Invite.used == False,
        Invite.expires_at > datetime.utcnow()
    ).update({"used": True})
    
    
    token = secrets.token_urlsafe(32)
    
    invite = Invite(
        user_id=user.id,
        token=token,
        role=user.role,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(invite)

    db.commit()

    send_admin_invite_email(email=user.email, token=token)
    
    create_super_admin_log(
        db = db,
        super_admin_id = current_user.id,
        action= f"RESENT_INVITE: {user.first_name} {user.last_name}",
        ip = request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {
        "status": "INVITE_RESENT"
    }
    


def fetch_communities(db: Session, current_user : User, request):
    communities = db.query(Community).all()
    return [
        {
            "id": c.id, 
            "display_name": c.display_name,
            "description" : c.description
        } 
        for c in communities
    ]



def get_dashboard_details(db: Session, current_user: User):
    community_count = db.query(Community).count()
    community_admin_count = db.query(CommunityAdmin).count()
    
    logs = (
        db.query(SuperAdminLogs)
        .filter(SuperAdminLogs.super_admin_id == current_user.id)
        .order_by(SuperAdminLogs.created_at.desc())
        .limit(10)
        .all()
    )
    
    return {
        "community_count": community_count,
        "community_admin_count": community_admin_count,
        "logs": [
            {
                "id" : log.id,
                "action" : log.action,
                "ip" : log.ip_address,
                "created_at" : log.created_at.isoformat()
            }
            for log in logs
        ]
    }