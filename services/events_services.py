from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    User, Member, Community, Events, EventRegistration
)

from utils.enums import RegistrationStatusEnum, EventStatusEnum


def get_all_events_service(db, current_user : User):
    
    member = db.query(Member).filter(Member.user_id == current_user.id).first()
    if not member:
        raise HTTPException(400, "You are not a member of any community")
    
    community = db.query(Community).filter(Community.id == member.community_id).first()
    if not community:
        raise HTTPException(400, "You are not a member of any community")
    
    events = db.query(Events).filter(Events.community_id == community.id).all()

    return events

def get_event_description(event_id : str, db, current_user : User):
    
    member = db.query(Member).filter(Member.user_id == current_user.id).first()
    if not member:
        raise HTTPException(400, "You are not a member of any community")
    
    community = db.query(Community).filter(Community.id == member.community_id).first()
    if not community:
        raise HTTPException(400, "You are not a member of any community")
    
    event = db.query(Events).filter(Events.id == event_id).first()
    
    if not event:
        raise HTTPException(404, "Event not found")
    
    return event



def register_for_event_service(event_id: str, db: Session, current_user: User):
    member = db.query(Member).filter(Member.user_id == current_user.id).first()
    if not member:
        raise HTTPException(400, "You are not a member of any community")

    event = db.query(Events).filter(
        Events.id == event_id,
        Events.community_id == member.community_id,
        Events.is_published == True
    ).first()
    if not event:
        raise HTTPException(404, "Event not found or not available")

    # Block registration for completed/cancelled events
    if event.status in (EventStatusEnum.completed, EventStatusEnum.cancelled):
        raise HTTPException(400, "Registration is closed for this event")

    existing = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.member_id == member.id
    ).first()

    if existing:
        if existing.status == RegistrationStatusEnum.registered:
            raise HTTPException(400, "You are already registered for this event")
        # Re-register if previously cancelled
        existing.status = RegistrationStatusEnum.registered
        db.commit()
        db.refresh(existing)
        return {"message": "Re-registered successfully", "registration_id": existing.id}

    registration = EventRegistration(
        event_id=event_id,
        member_id=member.id,
        status=RegistrationStatusEnum.registered
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    return {"message": "Registered successfully", "registration_id": registration.id}


def cancel_registration_service(event_id: str, db: Session, current_user: User):
    member = db.query(Member).filter(Member.user_id == current_user.id).first()
    if not member:
        raise HTTPException(400, "You are not a member of any community")

    registration = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.member_id == member.id,
        EventRegistration.status == RegistrationStatusEnum.registered
    ).first()

    if not registration:
        raise HTTPException(404, "No active registration found")

    registration.status = RegistrationStatusEnum.cancelled
    db.commit()

    return {"message": "Registration cancelled"}


def get_my_registrations_service(db: Session, current_user: User):
    member = db.query(Member).filter(Member.user_id == current_user.id).first()
    if not member:
        raise HTTPException(400, "You are not a member of any community")

    registrations = db.query(EventRegistration).filter(
        EventRegistration.member_id == member.id,
        EventRegistration.status == RegistrationStatusEnum.registered
    ).all()

    return {
        "registrations": [
            {
                "registration_id": r.id,
                "event_id": r.event_id,
                "registered_at": r.registered_at
            }
            for r in registrations
        ]
    }