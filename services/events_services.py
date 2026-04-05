from fastapi import HTTPException
from models import (
    User, Member, Community, Events
)


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