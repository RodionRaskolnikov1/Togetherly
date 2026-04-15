import secrets
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from models import (
    Community, User, Coordinator, 
    CommunityAdmin, Invite, AdminLogs,
    Events, CoordinatorLogs, Member, ProfileCommunity, Announcement,
    UserImage
)

from utils.hash import hash_password
from utils.enums import RoleEnum, EventStatusEnum
from utils.logs import create_admin_log
from utils.otp import send_coordinator_invite_email, send_member_invite
from utils.event_utils import auto_complete_events
from utils.file_utils import upload_event_poster
from models import EventImage

from datetime import datetime, timedelta, timezone

def get_dashboard_details(db : Session, current_user : User):
    
    admin = db.query(CommunityAdmin).filter(CommunityAdmin.user_id == current_user.id).first()
    
    if not admin:
        raise HTTPException(status_code=404, detail="Community admin not found")
    
    first_name = current_user.first_name
    community_name = admin.community.display_name
    
    coordinators_count = (
        db.query(Coordinator)
        .filter(Coordinator.community_admin_id == admin.id)
        .count()   
    )
    
    upcoming_events_count = (
        db.query(Events)
        .filter(Events.created_by == admin.id)
        .filter(Events.start_datetime > datetime.now(timezone.utc))
        .count()
    )
    
    upcoming_events = (
        db.query(Events)
        .filter(
            Events.community_id == admin.community_id,
            Events.is_published == True,
            Events.start_datetime > datetime.now()
        )
        .order_by(Events.start_datetime.asc())
        .limit(5)
        .all()
    )
    
    logs = (
        db.query(AdminLogs)
        .filter(AdminLogs.admin_id == admin.user_id)
        .order_by(AdminLogs.created_at.desc())
        .limit(10)
        .all()
    )
    
    members_count = (
        db.query(Member)
        .filter(Member.community_id == admin.community_id)
        .count()
    )
    profile_count = (
        db.query(ProfileCommunity)
        .filter(ProfileCommunity.community_id == admin.community_id)
        .count()
    )
    
    total_members = members_count + profile_count
    
    return {
        "first_name" : first_name,
        "community_name" : community_name,
        "total_members" : total_members,
        "coordinator_count" : coordinators_count,
        "upcoming_events_count" : upcoming_events_count,
        "upcoming_events" : [
            {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "location": event.location,
                "start_datetime": event.start_datetime,
                # "poster_image_url": event.poster_image_url,
                "poster_image_url": next(
                    (img.image_url for img in event.event_images if img.is_poster),
                    None
                )
            }
            for event in upcoming_events
        ],    
        "logs" : [
            {
                "id" : log.id,
                "action" : log.action,
                "ip" : log.ip_address,
                "created_at" : log.created_at.isoformat()
            }
            for log in logs
        ]
    }


def add_coordinator(payload, db: Session, current_user : User, request):
    
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    community = db.query(Community).filter(
        Community.id == admin.community_id
    ).first()
    
    if not community:
        raise HTTPException(400, "Invalid community")
    
    email = payload.user.email.strip()
    phone = payload.user.phone.strip() if payload.user.phone else None

    if phone == "":
        phone = None

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
    
    if not email:
        raise HTTPException(400, "Email is required for coordinator invitation")

    internal_password = secrets.token_urlsafe(32)

    try:
        user = User(
            email=email,
            phone=phone,
            password_hash=hash_password(internal_password),
            first_name=payload.user.first_name,
            father_name=payload.user.father_name,
            last_name=payload.user.last_name,
            dob=payload.user.dob,
            gender=payload.user.gender.value,
            role=RoleEnum.coordinator.value
        )
        db.add(user)
        db.flush()

        coordinator = Coordinator(
            user_id=user.id,
            community_id=community.id,
            community_admin_id=admin.id,
            is_active=True
        )
        db.add(coordinator)

        token = secrets.token_urlsafe(32)

        invite = Invite(
            user_id=user.id,
            token=token,
            role=user.role,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(invite)

        db.commit()
        db.refresh(coordinator)

        send_coordinator_invite_email(email=email, token=token)

        create_admin_log(
            db=db,
            admin_id=admin.user_id,
            action="COORDINATOR_INVITED",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return {
            "user_id": user.id,
            "coordinator_id": coordinator.id,
            "assigned_by": current_user.id,
            "status": "INVITE_SENT"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    
def toggle_coordinator_status_service(
    coordinator_id: str,
    db: Session,
    current_user,
    request
):
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    coordinator = db.query(Coordinator).filter(
        Coordinator.id == coordinator_id,
        Coordinator.community_admin_id == admin.id
    ).first()

    if not coordinator:
        raise HTTPException(404, "Coordinator not found or not authorized")

    coordinator.is_active = not coordinator.is_active
    db.commit()

    create_admin_log(
        db=db,
        admin_id=admin.user_id,
        action=f"COORDINATOR_STATUS_TOGGLED -> {coordinator.is_active}",
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {
        "coordinator_id": coordinator.id,
        "is_active": coordinator.is_active
    }
             
def fetch_coordinators_service(db: Session, current_user: User):

    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(status_code=404, detail="Community admin record not found")

    rows = (
        db.query(Coordinator, User, UserImage)
        .join(User, User.id == Coordinator.user_id)
        .outerjoin(UserImage, UserImage.user_id == User.id)
        .filter(Coordinator.community_admin_id == admin.id)
        .all()
    )

    return {
        "coordinators": [
            {
                "coordinator_id": coord.id,
                "image_url": userimg.image_url if userimg else None,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "gender": user.gender,
                "is_active": coord.is_active,
                "created_at": coord.created_at
            }
            for coord, user, userimg in rows
        ]
    }
    
def get_me_service(db : Session, current_user : User):
    
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()
    
    if not admin:
        raise HTTPException(400, "Community admin record not found")
        
    community = db.query(Community).filter(Community.id == admin.community_id).first()
    
    return {
        "first_name" : current_user.first_name,
        "last_name" : current_user.last_name,
        "email" : current_user.email,
        "gender" : current_user.gender,
        "community_name" : community.display_name
    }
    
def fetch_coordinator_logs_service(db : Session, coordinator_id : str, current_user : User):

    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")
    
    coordinator = db.query(Coordinator).filter(
        Coordinator.id == coordinator_id,
    ).first()
    
    if not coordinator:
        raise HTTPException(404, "Coordinator not found")

    logs = (
        db.query(CoordinatorLogs)
        .filter(CoordinatorLogs.coordinator_id == coordinator.user_id)
        .order_by(CoordinatorLogs.created_at.desc())
        .limit(10)
        .all()
    )
    
    return {
        "logs" : [
            {
                "id" : log.id,
                "action" : log.action,
                "ip" : log.ip_address,
                "created_at" : log.created_at.isoformat()
            }
            for log in logs
        ]
    }

def fetch_users_service(db : Session, current_user : User):

    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    from models.profile_community import ProfileCommunity
    from models.profile import Profile

    # Get profiles in the community
    rows = (
        db.query(ProfileCommunity, Profile, User)
        .join(Profile, Profile.id == ProfileCommunity.profile_id)
        .join(User, User.id == Profile.user_id)
        .filter(ProfileCommunity.community_id == admin.community_id)
        .all()
    )

    return {
        "users": [
            {
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": user.phone,
                "gender": user.gender,
                "profile_stage": profile.profile_stage,
                "joined_at": pc.joined_at.isoformat() if pc.joined_at else None,
                "verified_at": pc.verified_at.isoformat() if pc.verified_at else None
            }
            for pc, profile, user in rows
        ]
    }

def resend_invite_service(email : str, db : Session):

    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(404, "User not found")

    if (user.role != RoleEnum.coordinator.value):
        raise HTTPException(400, "User is not a coordinator")
    
    
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

    send_coordinator_invite_email(email=user.email, token=token)

    return {
        "status": "INVITE_RESENT"
    }
    
def create_event_service(payload, db : Session, current_user : User, request):
    
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    community = db.query(Community).filter(
        Community.id == admin.community_id
    ).first()
    
    if not community:
        raise HTTPException(400, "Invalid community")
    
    if payload.end_datetime <= payload.start_datetime:
        raise HTTPException(400, "End time must be after start time")

    try:
        event = Events(
            community_id = community.id,
            title = payload.title,
            description = payload.description,
            location = payload.location,
            start_datetime = payload.start_datetime,
            end_datetime = payload.end_datetime,
            status = EventStatusEnum.published,
            is_published = True,
            created_by = admin.id,
            poster_image_url = payload.poster_image_url
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        
        create_admin_log(
            db=db,
            admin_id=admin.user_id,
            action="CREATE_EVENT -> " + str(event.title),
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "events" : [
                {
                    "id" : event.id,
                    "title" : event.title,
                    "description" : event.description,
                    "location" : event.location,
                    "start_datetime" : event.start_datetime,
                    "end_datetime" : event.end_datetime,
                    "status" : event.status,
                    "is_published" : event.is_published,
                    "poster_image_url" : event.poster_image_url
                }
            ]
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
            
def list_events_service(db : Session, current_user : User, request):
    
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    community = db.query(Community).filter(
        Community.id == admin.community_id
    ).first()
    
    if not community:
        raise HTTPException(400, "Invalid community")
    
    auto_complete_events(db, community.id)
    
    events = db.query(Events).filter(Events.community_id == community.id).all()
    
    
    return {
        "events" : [    
            {
                "id" : event.id,
                "title" : event.title,
                "description" : event.description,
                "location" : event.location,
                "start_datetime" : event.start_datetime,
                "end_datetime" : event.end_datetime,
                "status" : event.status,
                "is_published" : event.is_published,
                # "poster_image_url": event.poster_image_url,
                "poster_image_url": next(
                    (img.image_url for img in event.event_images if img.is_poster),
                    None
                )
            }
            for event in events
        ]
    }

def upload_event_image_service(
    event_id: str,
    file: UploadFile,
    db: Session,
    current_user: User,
    request,
    is_poster: bool = False
):
    """Upload event image (can be multiple)"""
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    event = db.query(Events).filter(
        Events.id == event_id,
        Events.community_id == admin.community_id
    ).first()

    if not event:
        raise HTTPException(404, "Event not found or not authorized")

    image_url, public_id = upload_event_poster(file, event_id)
    
    event.poster_image_url = image_url
    event.poster_public_id = public_id
    # If this is set as poster, unset other poster images
    if is_poster:
        db.query(EventImage).filter(
            EventImage.event_id == event_id,
            EventImage.is_poster == True
        ).update({"is_poster": False})
    
    event_image = EventImage(
        event_id=event_id,
        image_url=image_url,
        public_id=public_id,
        is_poster=is_poster
    )
    db.add(event_image)
    db.commit()
    db.refresh(event_image)

    create_admin_log(
        db=db,
        admin_id=admin.user_id,
        action=f"UPLOAD_EVENT_IMAGE -> {event.title}",
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {
        "message": "Event image uploaded successfully",
        "image": {
            "id": event_image.id,
            "image_url": event_image.image_url,
            "is_poster": event_image.is_poster
        }
    }

def get_event_images_service(
    event_id: str,
    db: Session,
    current_user: User
):
    """Get all images for an event"""
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    event = db.query(Events).filter(
        Events.id == event_id,
        Events.community_id == admin.community_id
    ).first()

    if not event:
        raise HTTPException(404, "Event not found or not authorized")

    images = db.query(EventImage).filter(EventImage.event_id == event_id).all()

    return {
        "images": [
            {
                "id": img.id,
                "image_url": img.image_url,
                "is_poster": img.is_poster,
                "created_at": img.created_at.isoformat()
            }
            for img in images
        ]
    }

def set_event_poster_service(
    event_id: str,
    image_id: str,
    db: Session,
    current_user: User,
    request
):
    """Set an event image as the poster"""
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    event = db.query(Events).filter(
        Events.id == event_id,
        Events.community_id == admin.community_id
    ).first()

    if not event:
        raise HTTPException(404, "Event not found or not authorized")

    image = db.query(EventImage).filter(
        EventImage.id == image_id,
        EventImage.event_id == event_id
    ).first()

    if not image:
        raise HTTPException(404, "Image not found")

    # Unset all other poster images
    db.query(EventImage).filter(
        EventImage.event_id == event_id
    ).update({"is_poster": False})

    # Set this image as poster
    image.is_poster = True
    db.commit()
    db.refresh(image)

    create_admin_log(
        db=db,
        admin_id=admin.user_id,
        action=f"SET_EVENT_POSTER -> {event.title}",
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {
        "message": "Event poster set successfully",
        "image": {
            "id": image.id,
            "image_url": image.image_url,
            "is_poster": image.is_poster
        }
    }

def delete_event_image_service(
    event_id: str,
    image_id: str,
    db: Session,
    current_user: User,
    request
):
    """Delete an event image"""
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    event = db.query(Events).filter(
        Events.id == event_id,
        Events.community_id == admin.community_id
    ).first()

    if not event:
        raise HTTPException(404, "Event not found or not authorized")

    image = db.query(EventImage).filter(
        EventImage.id == image_id,
        EventImage.event_id == event_id
    ).first()

    if not image:
        raise HTTPException(404, "Image not found")

    db.delete(image)
    db.commit()

    create_admin_log(
        db=db,
        admin_id=admin.user_id,
        action=f"DELETE_EVENT_IMAGE -> {event.title}",
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {"message": "Image deleted successfully"}
    
    
def add_member_service(payload, db: Session, current_user: User, request):
    
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")
    
    community = db.query(Community).filter(
        Community.id == admin.community_id
    ).first()
    
    if not community:
        raise HTTPException(400, "Invalid community")
    
    email = payload.email.strip()
    phone = payload.phone.strip() if payload.phone else None

    if phone == "":
        phone = None

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
    
    if not email:
        raise HTTPException(400, "Email is required for coordinator invitation")
    
    internal_password = secrets.token_urlsafe(32)
    
    try: 
        user = User(
            email=email,
            phone=phone,
            password_hash=hash_password(internal_password),
            first_name=payload.first_name,
            father_name=payload.father_name,
            last_name=payload.last_name,
            dob=payload.dob,
            gender=payload.gender.value,
            role=RoleEnum.member.value
        )
        db.add(user)
        db.flush()
        
        member = Member(
            user_id = user.id,
            community_id = community.id,
            created_by = admin.id
        )
        db.add(member)
        
        invite_token = secrets.token_urlsafe(32)
        invite = Invite(
            user_id=user.id,
            token=invite_token,
            role=user.role,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(invite)
        
        send_member_invite(email=user.email, token = invite_token)
        db.commit()
        
        create_admin_log(
            db=db,
            admin_id=admin.user_id,
            action="ADD_MEMBER -> " + user.first_name + " " + user.last_name,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "message": f"{user.first_name} {user.last_name} added as member successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    

def get_members_service(db: Session, current_user: User):
    
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")
    
    
    community = db.query(Community).filter(
        Community.id == admin.community_id
    ).first()
    
    if not community:
        raise HTTPException(400, "Invalid community")
    
    
    members = (
        db.query(Member)
        .filter(Member.community_id == community.id)
        .all()
    )
    
    user_ids = [m.user_id for m in members]
    
    users = (
        db.query(User)
        .filter(User.id.in_(user_ids))
        .all()
    )
    
    return users    

def create_announcement_service(payload, db: Session, current_user: User, request):
    """Create a new announcement"""
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    community = db.query(Community).filter(
        Community.id == admin.community_id
    ).first()

    if not community:
        raise HTTPException(400, "Invalid community")

    try:
        announcement = Announcement(
            community_id=community.id,
            title=payload.title,
            content=payload.content,
            priority=payload.priority,
            is_pinned=payload.is_pinned,
            expires_at=payload.expires_at,
            status="draft",
            created_by=admin.id
        )
        db.add(announcement)
        db.commit()
        db.refresh(announcement)

        create_admin_log(
            db=db,
            admin_id=admin.user_id,
            action=f"CREATE_ANNOUNCEMENT -> {announcement.title}",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return {
            "announcements": [{
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content,
                "priority": announcement.priority,
                "status": announcement.status,
                "is_pinned": announcement.is_pinned,
                "created_by": announcement.created_by,
                "published_at": announcement.published_at,
                "expires_at": announcement.expires_at,
                "created_at": announcement.created_at,
                "updated_at": announcement.updated_at
            }]
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


def list_announcements_service(db: Session, current_user: User):
    """List all announcements for the admin's community"""
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    announcements = (
        db.query(Announcement)
        .filter(Announcement.community_id == admin.community_id)
        .order_by(Announcement.created_at.desc())
        .all()
    )

    return {
        "announcements": [{
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "priority": a.priority,
            "status": a.status,
            "is_pinned": a.is_pinned,
            "created_by": a.created_by,
            "published_at": a.published_at,
            "expires_at": a.expires_at,
            "created_at": a.created_at,
            "updated_at": a.updated_at
        } for a in announcements]
    }


def publish_announcement_service(announcement_id: str, db: Session, current_user: User, request):
    """Publish an announcement"""
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.community_id == admin.community_id
    ).first()

    if not announcement:
        raise HTTPException(404, "Announcement not found")

    announcement.status = "published"
    announcement.published_at = datetime.utcnow()
    db.commit()
    db.refresh(announcement)

    create_admin_log(
        db=db,
        admin_id=admin.user_id,
        action=f"PUBLISH_ANNOUNCEMENT -> {announcement.title}",
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {
        "announcements": [{
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "priority": announcement.priority,
            "status": announcement.status,
            "is_pinned": announcement.is_pinned,
            "created_by": announcement.created_by,
            "published_at": announcement.published_at,
            "expires_at": announcement.expires_at,
            "created_at": announcement.created_at,
            "updated_at": announcement.updated_at
        }]
    }


def delete_announcement_service(announcement_id: str, db: Session, current_user: User, request):
    """Delete an announcement"""
    admin = db.query(CommunityAdmin).filter(
        CommunityAdmin.user_id == current_user.id
    ).first()

    if not admin:
        raise HTTPException(400, "Community admin record not found")

    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.community_id == admin.community_id
    ).first()

    if not announcement:
        raise HTTPException(404, "Announcement not found")

    db.delete(announcement)
    db.commit()

    create_admin_log(
        db=db,
        admin_id=admin.user_id,
        action=f"DELETE_ANNOUNCEMENT -> {announcement.title}",
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {"message": "Announcement deleted successfully"}