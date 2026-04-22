from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from models import (
    User, Profile, Community, Coordinator, CommunityRequest, ProfileCommunity
    , ProfileImage, CoordinatorLogs, Announcement, Events
)

from utils.auth_utils import get_user_with_details
from utils.logs import create_coordinator_log
from utils.enums import AccountStatusEnum    
from utils.event_utils import auto_complete_events


def get_coordinator_logs_service(db: Session, current_user: User):
    """Fetch activity logs for the coordinator"""
    logs = (
        db.query(CoordinatorLogs)
        .filter(CoordinatorLogs.coordinator_id == current_user.id)
        .order_by(CoordinatorLogs.created_at.desc())
        .limit(50)
        .all()
    )
    
    return [
        {
            "id": log.id,
            "action": log.action,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]


def get_coordinator_reports_service(db: Session, current_user: User):
    """Fetch reports for the coordinator's community"""
    coordinator = db.query(Coordinator).filter_by(user_id=current_user.id, is_active=True).first()
    
    if not coordinator:
        return []
    
    # For now, return empty array - reports feature can be expanded 
    # when a Report model is added to the system
    # This can include: fake profiles, abusive behavior, etc.
    return []


def get_coordinator_dashboard_stats(db: Session, current_user: User):
    """Fetch comprehensive dashboard stats for coordinator"""
    coordinator = db.query(Coordinator).filter_by(user_id=current_user.id, is_active=True).first()
    
    if not coordinator:
        return {
            "total_members": 0,
            "pending_requests": 0,
            "suspended_members": 0,
            "reports": 0
        }
    
    # Get total verified members in community
    total_members = (
        db.query(ProfileCommunity)
        .filter(ProfileCommunity.community_id == coordinator.community_id)
        .count()
    )
    
    # Get pending requests
    pending_requests = (
        db.query(CommunityRequest)
        .filter(CommunityRequest.community_id == coordinator.community_id)
        .filter(CommunityRequest.status == "pending")
        .count()
    )
    
    # Get suspended/disabled members in community
    suspended_members = (
        db.query(User)
        .join(Profile, Profile.user_id == User.id)
        .join(ProfileCommunity, ProfileCommunity.profile_id == Profile.id)
        .filter(ProfileCommunity.community_id == coordinator.community_id)
        .filter(User.account_status == AccountStatusEnum.disabled)
        .count()
    )
    
    return {
        "total_members": total_members,
        "pending_requests": pending_requests,
        "suspended_members": suspended_members,
        "reports": 0  # Will be updated when reports model is implemented
    }
        
def get_coordinator_dashboard(db : Session, current_user : User):
       
    coordinator = db.query(Coordinator).filter_by(user_id=current_user.id, is_active=True).first()
    
    if not coordinator:
        raise HTTPException(403, "Coordinator account not found or inactive")
    
    total_members = (
        db.query(ProfileCommunity)
        .filter(ProfileCommunity.community_id == coordinator.community_id)
        .filter(ProfileCommunity.verified_by == current_user.id)
        .count()
    )
    
    pending_requests = (
        db.query(CommunityRequest)
        .filter(CommunityRequest.community_id == coordinator.community_id)
        .filter(CommunityRequest.status == "pending")
        .count()
    )
    
    
    return {
        "total_members": total_members,
        "pending_requests": pending_requests
    }
    
def fetch_community_requests(db: Session, current_user, request, status: str = "pending"):
   
   community_rows = (
        db.query(Coordinator.community_id)
        .filter(Coordinator.user_id == current_user.id)
        .all()
    )
   
   community_ids = [row.community_id for row in community_rows]

   query = (
        db.query(
            CommunityRequest.id.label("request_id"),
            User.first_name,
            User.last_name,
            Community.display_name.label("community_name"),
            CommunityRequest.status
        )
        .join(Profile, Profile.id == CommunityRequest.profile_id)
        .join(User, User.id == Profile.user_id)
        .join(Community, Community.id == CommunityRequest.community_id)
        .filter(CommunityRequest.community_id.in_(community_ids))
    )

   # Allow filtering by status; default is "pending" so coordinator sees actionable items first
   # Pass status="all" to get everything
   if status != "all":
        query = query.filter(CommunityRequest.status == status)

   results = query.all()

   return [
        {
            "request_id": r.request_id,
            "user_name": f"{r.first_name} {r.last_name}",
            "community_name": r.community_name,
            "status": r.status
        }
        for r in results
    ]
   
def decide_community_request(
        request_id: str,
        action: str,
        db: Session,
        request,
        current_user
    ):

    if action not in ["approve", "reject"]:
        raise HTTPException(400, "Invalid action. Must be 'approve' or 'reject'")

    req = db.query(CommunityRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")

    if req.status != "pending":
        raise HTTPException(400, "Request already processed")

    coordinator_check = db.query(Coordinator).filter_by(
        user_id=current_user.id,
        community_id=req.community_id,
        is_active=True
    ).first()

    if not coordinator_check:
        create_coordinator_log(
            db=db,
            coordinator_id=current_user.id,
            action=f"UNAUTHORIZED: Attempted to {action} request {request_id} for community {req.community_id} - coordinator not authorized or inactive",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        raise HTTPException(403, "Not authorized or coordinator account is inactive")

    profile = db.query(Profile).filter_by(id=req.profile_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")

    user_info = db.query(User).filter_by(id=profile.user_id).first()
    user_name = f"{user_info.first_name} {user_info.last_name}" if user_info else "Unknown User"

    try:
        if action == "approve":

            existing = db.query(ProfileCommunity).filter_by(
                profile_id=profile.id,
                community_id=req.community_id
            ).first()

            if existing:
                raise HTTPException(400, "User already joined this community")

            membership = ProfileCommunity(
                profile_id=profile.id,
                community_id=req.community_id,
                verified_by=current_user.id,
                verified_at=datetime.utcnow()
            )
            db.add(membership)

            req.status = "approved"
            profile.profile_stage = "verified"

            create_coordinator_log(
                db=db,
                coordinator_id=current_user.id,
                action=f"SUCCESS: Coordinator approved community request {request_id} for user {user_name} (ID: {profile.user_id})",
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )

        elif action == "reject":
            req.status = "rejected"
            profile.profile_stage = "rejected"

            create_coordinator_log(
                db=db,
                coordinator_id=current_user.id,
                action=f"SUCCESS: Coordinator rejected community request {request_id} for user {user_name} (ID: {profile.user_id})",
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )

        req.reviewed_by = current_user.id
        req.reviewed_at = datetime.utcnow()

        db.commit()

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to process request: {str(e)}")

    return {"message": f"Request {action}d successfully"}


def get_community_requests_service(request_id: str, db: Session, current_user : User, request):
    
    req = db.query(CommunityRequest).filter_by(id = request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")
    
    allowed = (
        db.query(Coordinator)
        .filter(
            Coordinator.user_id == current_user.id,
            Coordinator.community_id == req.community_id
        )
        .first()
    )

    if not allowed:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    profile = db.query(Profile).filter(Profile.id == req.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    user = get_user_with_details(profile.user_id, db)
    
    return user    
    
    
def get_members_service(db: Session, current_user : User):
    
    coordinator = db.query(Coordinator).filter_by(user_id=current_user.id, is_active=True).first()
    if not coordinator:
        raise HTTPException(403, "Not authorized or coordinator account is inactive")

    members = (
        db.query(User, ProfileImage.image_url)
        .join(Profile, Profile.user_id == User.id)
        .join(ProfileCommunity, ProfileCommunity.profile_id == Profile.id)
        .outerjoin(
            ProfileImage,
            and_(
                ProfileImage.profile_id == Profile.id,
                ProfileImage.is_primary == True
            )
        )
        .filter(ProfileCommunity.community_id == coordinator.community_id)
        .all()
    )

    result = []

    for user, image_url in members:
        result.append({
            "id": user.id,
            "first_name": user.first_name,
            "father_name": user.father_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "account_status": user.account_status,
            "phone_verified": user.phone_verified,
            "profile_photo": image_url
        })

    return result



def get_member_details_service(user_id: str, db : Session, current_user : User):

    coordinator = db.query(Coordinator).filter_by(user_id=current_user.id, is_active=True).first()
    if not coordinator:
        raise HTTPException(403, "Not authorized or coordinator account is inactive")

    user = get_user_with_details(user_id, db)

    return user

def get_coordinator_events_service(db: Session, current_user: User):
    """Fetch all events for the coordinator's community"""
    coordinator = db.query(Coordinator).filter_by(user_id=current_user.id, is_active=True).first()
    if not coordinator:
        raise HTTPException(403, "Not authorized or coordinator account is inactive")

    # Auto complete past events
    auto_complete_events(db, coordinator.community_id)

    events = (
        db.query(Events)
        .filter(Events.community_id == coordinator.community_id)
        .order_by(Events.start_datetime.desc())
        .all()
    )

    return {
        "events": [
            {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "location": event.location,
                "start_datetime": event.start_datetime,
                "end_datetime": event.end_datetime,
                "status": event.status,
                "is_published": event.is_published,
                "poster_image_url": next(
                    (img.image_url for img in event.event_images if img.is_poster),
                    None
                )
            }
            for event in events
        ]
    }


def get_coordinator_event_detail_service(event_id: str, db: Session, current_user: User):
    """Fetch a single event detail for the coordinator's community"""
    coordinator = db.query(Coordinator).filter_by(user_id=current_user.id, is_active=True).first()
    if not coordinator:
        raise HTTPException(403, "Not authorized or coordinator account is inactive")

    event = (
        db.query(Events)
        .filter(
            Events.id == event_id,
            Events.community_id == coordinator.community_id
        )
        .first()
    )

    if not event:
        raise HTTPException(404, "Event not found or does not belong to your community")

    registrations_count = len([
        r for r in event.registrations
        if r.status.value == "registered"
    ]) if event.registrations else 0

    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "location": event.location,
        "start_datetime": event.start_datetime,
        "end_datetime": event.end_datetime,
        "status": event.status,
        "is_published": event.is_published,
        "poster_image_url": next(
            (img.image_url for img in event.event_images if img.is_poster),
            None
        ),
        "images": [
            {
                "id": img.id,
                "image_url": img.image_url,
                "is_poster": img.is_poster
            }
            for img in event.event_images
        ],
        "total_registrations": registrations_count
    }


def get_coordinator_me_service(db: Session, current_user: User):
    """Fetch the coordinator's own profile info"""
    coordinator = db.query(Coordinator).filter_by(user_id=current_user.id, is_active=True).first()
    if not coordinator:
        raise HTTPException(403, "Not authorized or coordinator account is inactive")

    community = coordinator.community

    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "father_name": current_user.father_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "gender": current_user.gender,
        "dob": current_user.dob,
        "account_status": current_user.account_status,
        "phone_verified": current_user.phone_verified,
        "email_verified": current_user.email_verified,
        "coordinator_id": coordinator.id,
        "is_active": coordinator.is_active,
        "joined_at": coordinator.created_at,
        "community": {
            "id": community.id,
            "name": community.display_name
        } if community else None
    }


def get_coordinator_announcements_service(db: Session, current_user: User):
    """Fetch all announcements for the coordinator's community"""
    coordinator = db.query(Coordinator).filter_by(user_id=current_user.id, is_active=True).first()
    if not coordinator:
        raise HTTPException(403, "Not authorized or coordinator account is inactive")

    announcements = (
        db.query(Announcement)
        .filter(Announcement.community_id == coordinator.community_id)
        .filter(Announcement.status == "published")
        .order_by(Announcement.is_pinned.desc(), Announcement.published_at.desc())
        .all()
    )

    return {
        "announcements": [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "priority": a.priority,
                "status": a.status,
                "is_pinned": a.is_pinned,
                "published_at": a.published_at,
                "expires_at": a.expires_at,
                "created_at": a.created_at
            }
            for a in announcements
        ]
    }