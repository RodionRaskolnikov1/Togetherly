from datetime import timezone, datetime
from sqlalchemy.orm import Session
from models import (
    Events
)
from utils.enums import EventStatusEnum

def auto_complete_events(db : Session, community_id : str):
    now = datetime.now(timezone.utc)
    
    events = db.query(Events).filter(
        Events.community_id == community_id,
        Events.status == EventStatusEnum.published,
        Events.end_datetime < now
    ).all()
    
    
    for event in events:
        event.status = EventStatusEnum.completed
        
    if events:
        db.commit()
    