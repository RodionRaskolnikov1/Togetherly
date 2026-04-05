from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

from utils.auth_utils import get_current_user

from services.events_services import (
    get_all_events_service,
    get_event_description
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/all-events")
def get_all_events(
        db : Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return get_all_events_service(db, current_user)

@router.get("/{event_id}")
def get_event(
        event_id : str,
        db : Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return get_event_description(event_id, db, current_user)


