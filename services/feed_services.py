from fastapi import HTTPException, status, BackgroundTasks
from datetime import datetime, timezone, timedelta, date
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, Session
from sqlalchemy import true, or_, and_

from models import (
    Profile, User, Lifestyle,
    ProfessionDetails, EducationDetails,
    ProfileCommunity, PermanentAddress, 
    FamilyDetails, ProfileConnections,
    UserBlock, SupportTicket, AppFeedback,
    UserPreference, CurrentAddress, Country,
    ProfileImage, UserSettings, ProfileFavourite, WorkAddress, user
)

from utils.enums import (
    ConnectionRequestEnum,
    VisibilityEnum
)

from utils.mail import (
    send_support_emails 
)

from schemas.settings_schema import UserPreferenceCreate
from schemas.dashboardSchema import FeedUserOut

MAX_FAVOURITES = 10
PENDING_EXPIRY_HOURS = 24

def get_suggested_profiles(
        db: Session,
        current_user: User,
        min_age: int | None,
        max_age: int | None,
        min_height: int | None,
        max_height: int | None,
        min_income: int | None,
        max_income: int | None,
        marital_status,
        city_id: str | None,
        sub_caste_id: str | None,
        education_level: str | None,
        verified_only: bool,
        family_type,
        family_status,
        employment_status
    ):
    
    if not current_user.dob:
        raise HTTPException(400, "DOB not set")
    

    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(400, "Profile not found")
    
    preference = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()

    today = date.today()

    current_age = today.year - current_user.dob.year - (
        (today.month, today.day) < (current_user.dob.month, current_user.dob.day)
    )


    effective_min_age = min_age if min_age is not None \
        else (preference.min_age if (preference and preference.min_age is not None) else (current_age - 4))
        
    effective_max_age = max_age if max_age is not None \
        else (preference.max_age if (preference and preference.max_age is not None) else (current_age + 4))
    
    effective_min_income = min_income if min_income is not None else (preference.min_income if preference else None)
    effective_max_income = max_income if max_income is not None else (preference.max_income if preference else None)

    effective_diet = preference.diet_preference if preference else None
    
    query = (
        db.query(User)
        .join(Profile, Profile.user_id == User.id)
        .outerjoin(Lifestyle, Lifestyle.profile_id == Profile.id)
        .outerjoin(PermanentAddress, PermanentAddress.profile_id == Profile.id)
        .outerjoin(CurrentAddress, CurrentAddress.profile_id == Profile.id) 
        .outerjoin(ProfessionDetails, ProfessionDetails.profile_id == Profile.id)
        .outerjoin(WorkAddress, WorkAddress.profession_id == ProfessionDetails.id)
        .outerjoin(FamilyDetails, FamilyDetails.profile_id == Profile.id)
        .outerjoin(EducationDetails, EducationDetails.profile_id == Profile.id)
        .options(
            joinedload(User.profile).joinedload(Profile.education_details),
            joinedload(User.profile).joinedload(Profile.profession_details).joinedload(ProfessionDetails.work_address),
            joinedload(User.profile).joinedload(Profile.lifestyle),
            joinedload(User.profile).joinedload(Profile.current_address),
            joinedload(User.profile).joinedload(Profile.permanent_address),
            joinedload(User.profile).joinedload(Profile.horoscope),
            joinedload(User.profile).joinedload(Profile.family_details),
            joinedload(User.profile).joinedload(Profile.communities)
                .joinedload(ProfileCommunity.community),
            joinedload(User.profile).joinedload(Profile.profile_images),
        )
        .filter(User.gender != current_user.gender)
        .filter(Profile.id != profile.id)
    )
    
    if profile.religion_id:
        query = query.filter(Profile.religion_id == profile.religion_id)
    if profile.caste_id:
        query = query.filter(Profile.caste_id == profile.caste_id)

    
    if city_id:
        query = query.filter(PermanentAddress.city_id == city_id)
    if sub_caste_id:
        query = query.filter(Profile.sub_caste_id == sub_caste_id)
    if marital_status:
        query = query.filter(Profile.marital_status.in_(marital_status))
    if family_type:
        query = query.filter(FamilyDetails.family_type == family_type)
    if family_status:
        query = query.filter(FamilyDetails.family_status == family_status)
    if employment_status:
        query = query.filter(ProfessionDetails.employment_status == employment_status)
    if min_height:
        query = query.filter(Lifestyle.height >= min_height)
    if max_height:
        query = query.filter(Lifestyle.height <= max_height)
    if education_level:
        query = query.filter(EducationDetails.level == education_level)
    if verified_only:
        query = query.filter(User.account_status.in_(["phone_verified", "email_verified", "active"]))
        
        
    max_dob = today - timedelta(days=effective_min_age * 365)
    min_dob = today - timedelta(days=effective_max_age * 365)
    query = query.filter(User.dob.between(min_dob, max_dob))
            
    if effective_min_income:
        query = query.filter(
            or_(ProfessionDetails.annual_income >= effective_min_income, ProfessionDetails.annual_income == None)
        )
        
    if effective_max_income:
        query = query.filter(
            or_(ProfessionDetails.annual_income <= effective_max_income, ProfessionDetails.annual_income == None)
        )

    if effective_diet:
        query = query.filter(
            or_(Lifestyle.diet == effective_diet, Lifestyle.diet == None)
        )
        
        

    effective_nri = preference.NRI if (preference and preference.NRI is True) else None        
        
    if effective_nri is True:
        INDIA_COUNTRY_ID = db.query(Country.id).filter(Country.name == "India").scalar()
        query = query.filter(CurrentAddress.country_id != INDIA_COUNTRY_ID)
        
    
    blocked_ids = (
        db.query(UserBlock.blocked_user_id)
        .filter(UserBlock.blocker_id == current_user.id)
        .subquery()
    )

    blockers_ids = (
        db.query(UserBlock.blocker_id)
        .filter(UserBlock.blocked_user_id == current_user.id)
        .subquery()
    )
    
    query = query.filter(User.id.notin_(blocked_ids))
    query = query.filter(User.id.notin_(blockers_ids))

    current_profile_id = profile.id
    
    sent_connection_map = {
        c.receiver_id: c.status
        for c in db.query(ProfileConnections).filter(
            ProfileConnections.sender_id == current_profile_id
        ).all()
    }
    
    received_connection_map = {
        c.sender_id: c.status
        for c in db.query(ProfileConnections).filter(
            ProfileConnections.receiver_id == current_profile_id
        ).all()
    }
    
    favourite_ids = {
        f.favourite_user_id
        for f in db.query(ProfileFavourite).filter(
            ProfileFavourite.user_id == current_user.id
        ).all()
    }
    
    users = query.distinct().limit(20).all()

    result = []
    for u in users:
        p = u.profile
        other_profile_id = p.id if p else None

        connection_status = None
        connection_direction = None

        sent = sent_connection_map.get(other_profile_id)
        received = received_connection_map.get(other_profile_id)

        if sent and received:
            if sent == ConnectionRequestEnum.accepted and received == ConnectionRequestEnum.accepted:
                connection_status = "mutual"
                connection_direction = "mutual"
            else:
                connection_status = sent.value
                connection_direction = "sent_pending_reverse"
        elif sent:
            connection_status = sent.value
            connection_direction = "sent"
        elif received:
            connection_status = received.value
            connection_direction = "received"

        result.append({
            "user": FeedUserOut.model_validate(u),  
            "meta": {
                "connection_status": connection_status,       
                "connection_direction": connection_direction, 
                "is_favourite": u.id in favourite_ids,
                "visibility": u.settings.visibility if u.settings else None,
            }
        })

    return result




def _auto_create_reverse(db, from_profile, to_profile):
    reverse_existing = db.query(ProfileConnections).filter(
        ProfileConnections.sender_id == to_profile.id,
        ProfileConnections.receiver_id == from_profile.id
    ).first()

    if reverse_existing:
        return reverse_existing  

    from_settings = db.query(UserSettings).filter(
        UserSettings.user_id == from_profile.user_id
    ).first()
    from_visibility = from_settings.visibility if from_settings else VisibilityEnum.public

    if from_visibility == VisibilityEnum.public:
        reverse = ProfileConnections(
            sender_id=to_profile.id,
            receiver_id=from_profile.id,
            status=ConnectionRequestEnum.accepted,
            responded_at=datetime.now(timezone.utc)
        )
    else:
        reverse = ProfileConnections(
            sender_id=to_profile.id,
            receiver_id=from_profile.id,
            status=ConnectionRequestEnum.pending
        )

    db.add(reverse)
    return reverse


def send_connection_request(db, profile_id, current_user):

    sender_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not sender_profile:
        raise HTTPException(400, "Sender profile not found")

    receiver_profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not receiver_profile:
        raise HTTPException(400, "Receiver profile not found")

    if sender_profile.id == receiver_profile.id:
        raise HTTPException(400, "You cannot send a request to yourself")

    existing = db.query(ProfileConnections).filter(
        ProfileConnections.sender_id == sender_profile.id,
        ProfileConnections.receiver_id == receiver_profile.id
    ).first()

    if existing:
        if existing.status == ConnectionRequestEnum.accepted:
            raise HTTPException(400, "You have already sent a request that was accepted")
        if existing.status == ConnectionRequestEnum.pending:
            raise HTTPException(400, "Your request to this person is already pending")
        if existing.status == ConnectionRequestEnum.rejected:
            try:
                existing.status = ConnectionRequestEnum.pending
                existing.responded_at = None
                
                db.query(ProfileConnections).filter(
                    ProfileConnections.sender_id == receiver_profile.id,
                    ProfileConnections.receiver_id == sender_profile.id
                ).delete(synchronize_session=False)

                db.commit()
                return {"message": "Connection request re-sent successfully", "connected": False}
            except SQLAlchemyError:
                db.rollback()
                raise HTTPException(500, "Failed to resend connection request")

    receiver_settings = db.query(UserSettings).filter(
        UserSettings.user_id == receiver_profile.user_id
    ).first()
    receiver_visibility = receiver_settings.visibility if receiver_settings else VisibilityEnum.public

    try:
        if receiver_visibility == VisibilityEnum.public:
            connection = ProfileConnections(
                sender_id=sender_profile.id,
                receiver_id=receiver_profile.id,
                status=ConnectionRequestEnum.accepted,
                responded_at=datetime.now(timezone.utc)
            )
            db.add(connection)

            _auto_create_reverse(db, from_profile=sender_profile, to_profile=receiver_profile)

            db.commit()
            return {"message": "Connected successfully", "connected": True}
        else:
            connection = ProfileConnections(
                sender_id=sender_profile.id,
                receiver_id=receiver_profile.id,
                status=ConnectionRequestEnum.pending
            )
            db.add(connection)
            db.commit()
            return {"message": "Connection request sent successfully", "connected": False}

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Failed to send connection request")
 
 
def get_connection_requests(db, current_user):

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(400, "Profile not found")

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=PENDING_EXPIRY_HOURS)).replace(tzinfo=None)

    blocked_ids = {
        r.blocked_user_id
        for r in db.query(UserBlock).filter(UserBlock.blocker_id == current_user.id).all()
    }
    blocker_ids = {
        r.blocker_id
        for r in db.query(UserBlock).filter(UserBlock.blocked_user_id == current_user.id).all()
    }
    
    rows = (
        db.query(ProfileConnections, User)
        .join(Profile, Profile.id == ProfileConnections.sender_id)
        .join(User, User.id == Profile.user_id)
        .options(
            joinedload(User.profile).joinedload(Profile.education_details),
            joinedload(User.profile).joinedload(Profile.profession_details).joinedload(ProfessionDetails.work_address),
            joinedload(User.profile).joinedload(Profile.lifestyle),
            joinedload(User.profile).joinedload(Profile.current_address),
            joinedload(User.profile).joinedload(Profile.permanent_address),
            joinedload(User.profile).joinedload(Profile.horoscope),
            joinedload(User.profile).joinedload(Profile.family_details),
            joinedload(User.profile).joinedload(Profile.communities)
                .joinedload(ProfileCommunity.community),
            joinedload(User.profile).joinedload(Profile.profile_images),
            joinedload(User.settings),
        )
        .filter(
            ProfileConnections.receiver_id == profile.id,
            ProfileConnections.status == ConnectionRequestEnum.pending,
            ProfileConnections.created_at >= cutoff
        )
        .all()
    )

    requests = []
    for conn, user in rows:
        visibility = user.settings.visibility if user.settings else VisibilityEnum.public
        
        if user.id in blocked_ids or user.id in blocker_ids:
            continue

        if visibility == VisibilityEnum.public:
            # Full profile — same as feed
            requests.append({
                "connection_id": conn.id,
                "sender_profile_id": conn.sender_id,
                "sent_at": conn.created_at,
                "visibility": "public",
                "user": FeedUserOut.model_validate(user),  
            })
        else:
            # Private — sirf basic info
            p = user.profile
            primary_image = next(
                (img.image_url for img in p.profile_images if img.is_primary),
                None
            ) if p and p.profile_images else None

            requests.append({
                "connection_id": conn.id,
                "sender_profile_id": conn.sender_id,
                "sent_at": conn.created_at,
                "visibility": "private",
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "profile_image": primary_image,
                    "age": (
                        date.today().year - user.dob.year - (
                            (date.today().month, date.today().day) < (user.dob.month, user.dob.day)
                        )
                    ) if user.dob else None,
                }
            })

    return {
        "count": len(requests),
        "requests": requests
    }
 
 
def respond_to_connection_request(db, connection_id: str, action: str, current_user):

    if action not in ("accept", "reject"):
        raise HTTPException(400, "Action must be 'accept' or 'reject'")

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(400, "Profile not found")

    connection = db.query(ProfileConnections).filter(
        ProfileConnections.id == connection_id,
        ProfileConnections.receiver_id == profile.id,
        ProfileConnections.status == ConnectionRequestEnum.pending
    ).first()

    if not connection:
        raise HTTPException(404, "Pending connection request not found")

    try:
        if action == "accept":
            connection.status = ConnectionRequestEnum.accepted
            connection.responded_at = datetime.now(timezone.utc)
            db.flush()  # write this before creating reverse

            # Auto-trigger reverse: receiver → sender
            sender_profile = db.query(Profile).filter(
                Profile.id == connection.sender_id
            ).first()

            _auto_create_reverse(db, from_profile=sender_profile, to_profile=profile)

        else:
            connection.status = ConnectionRequestEnum.rejected
            connection.responded_at = datetime.now(timezone.utc)

        db.commit()
        return {
            "message": f"Connection request {'accepted' if action == 'accept' else 'rejected'}",
            "connection_id": connection_id,
            "status": connection.status.value
        }
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Failed to update connection request")
 
 
def get_my_connections(db, current_user):

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(400, "Profile not found")
    
    
    blocked_ids = {
        r.blocked_user_id
        for r in db.query(UserBlock).filter(UserBlock.blocker_id == current_user.id).all()
    }
    blocker_ids = {
        r.blocker_id
        for r in db.query(UserBlock).filter(UserBlock.blocked_user_id == current_user.id).all()
    }
    
    # Rows where I am the sender and it's accepted
    sent_accepted = db.query(ProfileConnections).filter(
        ProfileConnections.sender_id == profile.id,
        ProfileConnections.status == ConnectionRequestEnum.accepted
    ).all()

    # Rows where I am the receiver and it's accepted
    received_accepted = db.query(ProfileConnections).filter(
        ProfileConnections.receiver_id == profile.id,
        ProfileConnections.status == ConnectionRequestEnum.accepted
    ).all()

    # Mutual = other person's ID appears in BOTH sets
    sent_to = {conn.receiver_id: conn for conn in sent_accepted}
    received_from = {conn.sender_id: conn for conn in received_accepted}

    mutual_ids = set(sent_to.keys()) & set(received_from.keys())

    if not mutual_ids:
        return {"count": 0, "connections": []}

    profiles = {
        p.id: p for p in db.query(Profile).filter(Profile.id.in_(mutual_ids)).all()
    }

    users = (
        db.query(User)
        .join(Profile, Profile.user_id == User.id)
        .outerjoin(Lifestyle, Lifestyle.profile_id == Profile.id)
        .outerjoin(PermanentAddress, PermanentAddress.profile_id == Profile.id)
        .outerjoin(CurrentAddress, CurrentAddress.profile_id == Profile.id)
        .outerjoin(ProfessionDetails, ProfessionDetails.profile_id == Profile.id)
        .outerjoin(WorkAddress, WorkAddress.profession_id == ProfessionDetails.id)
        .outerjoin(FamilyDetails, FamilyDetails.profile_id == Profile.id)
        .outerjoin(EducationDetails, EducationDetails.profile_id == Profile.id)
        .options(
            joinedload(User.profile).joinedload(Profile.education_details),
            joinedload(User.profile).joinedload(Profile.profession_details).joinedload(ProfessionDetails.work_address),
            joinedload(User.profile).joinedload(Profile.lifestyle),
            joinedload(User.profile).joinedload(Profile.current_address),
            joinedload(User.profile).joinedload(Profile.permanent_address),
            joinedload(User.profile).joinedload(Profile.horoscope),
            joinedload(User.profile).joinedload(Profile.family_details),
            joinedload(User.profile).joinedload(Profile.communities)
                .joinedload(ProfileCommunity.community),
            joinedload(User.profile).joinedload(Profile.profile_images),
        )
        .filter(Profile.id.in_(mutual_ids))
        .all()
    )

    result = []
    for u in users:
        p = u.profile
        
        if u.id in blocked_ids or u.id in blocker_ids:
            continue

        conn = sent_to[p.id]
        result.append({
            "connection_id": conn.id,
            "connected_at": conn.responded_at,
            "user": FeedUserOut.model_validate(u),  
        })

    return {"count": len(result), "connections": result}
 
 
def remove_connection(db, connection_id: str, current_user):

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(400, "Profile not found")

    # Find the specific connection row first to identify the other party
    connection = db.query(ProfileConnections).filter(
        ProfileConnections.id == connection_id,
        ProfileConnections.status == ConnectionRequestEnum.accepted,
        or_(
            ProfileConnections.sender_id == profile.id,
            ProfileConnections.receiver_id == profile.id
        )
    ).first()

    if not connection:
        raise HTTPException(404, "Connection not found")

    # Identify the other person
    other_id = connection.receiver_id if connection.sender_id == profile.id else connection.sender_id

    # Delete BOTH directional rows
    try:
        db.query(ProfileConnections).filter(
            or_(
                and_(ProfileConnections.sender_id == profile.id, ProfileConnections.receiver_id == other_id),
                and_(ProfileConnections.sender_id == other_id, ProfileConnections.receiver_id == profile.id)
            )
        ).delete(synchronize_session=False)
        db.commit()
        return {"message": "Connection removed"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Failed to remove connection")
    

def get_pending_requests(db, current_user):
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(400, "Profile not found")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=PENDING_EXPIRY_HOURS)

    # Block logic
    blocked_ids = {
        r.blocked_user_id
        for r in db.query(UserBlock).filter(UserBlock.blocker_id == current_user.id).all()
    }
    blocker_ids = {
        r.blocker_id
        for r in db.query(UserBlock).filter(UserBlock.blocked_user_id == current_user.id).all()
    }

    rows = (
        db.query(ProfileConnections, User)
        .join(Profile, Profile.id == ProfileConnections.sender_id)
        .join(User, User.id == Profile.user_id)
        .options(
            joinedload(User.profile).joinedload(Profile.education_details),
            joinedload(User.profile).joinedload(Profile.profession_details).joinedload(ProfessionDetails.work_address),
            joinedload(User.profile).joinedload(Profile.lifestyle),
            joinedload(User.profile).joinedload(Profile.current_address),
            joinedload(User.profile).joinedload(Profile.permanent_address),
            joinedload(User.profile).joinedload(Profile.horoscope),
            joinedload(User.profile).joinedload(Profile.family_details),
            joinedload(User.profile).joinedload(Profile.communities)
                .joinedload(ProfileCommunity.community),
            joinedload(User.profile).joinedload(Profile.profile_images),
            joinedload(User.settings),
        )
        .filter(
            ProfileConnections.receiver_id == profile.id,
            ProfileConnections.status == ConnectionRequestEnum.pending,
            ProfileConnections.created_at < cutoff   # only old pending
        )
        .all()
    )

    requests = []

    for conn, user in rows:

        # Skip blocked users
        if user.id in blocked_ids or user.id in blocker_ids:
            continue

        visibility = user.settings.visibility if user.settings else VisibilityEnum.public

        if visibility == VisibilityEnum.public:
            requests.append({
                "connection_id": conn.id,
                "sender_profile_id": conn.sender_id,
                "sent_at": conn.created_at,
                "visibility": "public",
                "user": FeedUserOut.model_validate(user),
            })
        else:
            p = user.profile

            primary_image = next(
                (img.image_url for img in p.profile_images if img.is_primary),
                None
            ) if p and p.profile_images else None

            age = None
            if user.dob:
                today = date.today()
                age = today.year - user.dob.year - (
                    (today.month, today.day) < (user.dob.month, user.dob.day)
                )

            requests.append({
                "connection_id": conn.id,
                "sender_profile_id": conn.sender_id,
                "sent_at": conn.created_at,
                "visibility": "private",
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "profile_image": primary_image,
                    "age": age,
                }
            })

    return {
        "count": len(requests),
        "requests": requests
    }
   

def get_blocked_users(db : Session, current_user):
    
    blocked = (
        db.query(
            User.id,
            User.first_name,
            User.last_name,
            ProfileImage.image_url
        )
        .join(UserBlock, UserBlock.blocked_user_id == User.id)
        .join(Profile, Profile.user_id == User.id)
        .outerjoin(ProfileImage, (ProfileImage.profile_id == Profile.id) & (ProfileImage.is_primary == true()))
        .filter(UserBlock.blocker_id == current_user.id)
        .all()
    )
    
    return [row._asdict() for row in blocked]



def block_user_service(db : Session, current_user, user_id):
    
    if current_user.id == user_id:
        raise HTTPException(400, "Cannot block yourself")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(404, "User not found")
    
    existing = db.query(UserBlock).filter(
        UserBlock.blocker_id == current_user.id,
        UserBlock.blocked_user_id == user_id
    ).first()
    if existing:
        raise HTTPException(400, "User already blocked")

    block = UserBlock(blocker_id=current_user.id, blocked_user_id=user_id)
    db.add(block)
    db.commit()
    
    return {"message": "User blocked successfully"}

def unblock_user_service(db: Session, current_user: User, user_id: str):
    
    block = db.query(UserBlock).filter(
        UserBlock.blocker_id == current_user.id,
        UserBlock.blocked_user_id == user_id
    ).first()
    
    if not block:
        raise HTTPException(404, "Block record not found")
    
    db.delete(block)
    db.commit()
    return {"message": "User unblocked successfully"}


def create_support_ticket_service(db: Session, current_user: User, payload, background_tasks: BackgroundTasks):

    now = datetime.now(timezone.utc)

    recent_ticket = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.user_id == current_user.id,
            SupportTicket.created_at >= now - timedelta(minutes=2)
        )
        .first()
    )
    
    if recent_ticket is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before sending another support request."
        )

    ticket = SupportTicket(
        user_id=current_user.id,
        subject=payload.subject,
        message=payload.message
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    background_tasks.add_task(
        send_support_emails,
        user_email=current_user.email,
        subject=payload.subject,
        message=payload.message,
        ticket_id=ticket.id
    )

    return {
        "message": "Support request submitted successfully.",
        "ticket_id": ticket.id
    }
    


def submit_feedback_service(db: Session, current_user, payload, background_tasks: BackgroundTasks):

    recent = (
        db.query(AppFeedback)
        .filter(
            AppFeedback.user_id == current_user.id,
            AppFeedback.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        )
        .first()
    )

    if recent is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have already submitted feedback recently."
        )

    feedback = AppFeedback(
        user_id=current_user.id,
        rating=payload.rating,
        message=payload.message
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {
        "message": "Thank you for your feedback!",
        "feedback_id": feedback.id
    }
    

def get_or_create_preference(db: Session, current_user : User) -> UserPreference:
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not pref:
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref



def update_preference(db: Session, current_user : User, data: UserPreferenceCreate) -> UserPreference:
    
    pref = get_or_create_preference(db, current_user)
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pref, field, value)
    
    db.commit()
    db.refresh(pref)
    return pref



def set_favourites_service(
    user_ids: list[str],
    db: Session,
    current_user
):
    if len(user_ids) > MAX_FAVOURITES:
        raise HTTPException(400, f"Cannot favourite more than {MAX_FAVOURITES} profiles")

    # dedupe
    user_ids = list(set(user_ids))

    # ✅ self-favourite check using current_user.id directly, no profile query needed
    if current_user.id in user_ids:
        raise HTTPException(400, "Cannot favourite your own profile")

    # ✅ validate all user_ids exist in users table
    target_users = db.query(User).filter(User.id.in_(user_ids)).all()
    if len(target_users) != len(user_ids):
        raise HTTPException(404, "One or more users not found")

    # ✅ wipe and replace
    db.query(ProfileFavourite).filter(
        ProfileFavourite.user_id == current_user.id
    ).delete()

    new_favourites = [
        ProfileFavourite(
            user_id=current_user.id,
            favourite_user_id=uid
        )
        for uid in user_ids
    ]
    db.bulk_save_objects(new_favourites)
    db.commit()

    return {
        "message": "Favourites updated successfully",
        "count": len(new_favourites),
        "favourites": user_ids
    }