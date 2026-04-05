from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session

from services.community_admin_services import  (
        add_coordinator, fetch_coordinator_logs_service, 
        fetch_coordinators_service, fetch_users_service, get_me_service, 
        toggle_coordinator_status_service, resend_invite_service,
        create_event_service, list_events_service, get_dashboard_details,
        upload_event_image_service, get_event_images_service, 
        set_event_poster_service, delete_event_image_service,
        add_member_service, get_members_service,
        create_announcement_service, list_announcements_service,
        publish_announcement_service, delete_announcement_service
    
    )

from schemas.coordinatorSchema import CoordinatorCreate
from schemas.eventSchema import EventCreate, EventResponse
from schemas.userSchema import MemberCreate
from schemas.announcementSchema import AnnouncementCreate
from database import get_db
from utils.auth_utils import require_community_admin

router = APIRouter(prefix="/community-admin", tags=["community-admin"])

@router.get("/dashboard")
def get_dashboard(db : Session = Depends(get_db), current_user = Depends(require_community_admin)):
    return get_dashboard_details(db, current_user)

@router.post("/register-coordinator")
def register_coordinator(payload: CoordinatorCreate, request: Request, db : Session = Depends(get_db), current_user = Depends(require_community_admin)):
    return add_coordinator(payload, db, current_user, request)

@router.post("/coordinators/{coordinator_id}/toggle")
def toggle_coordinator_status(
        coordinator_id: str,
        request: Request,
        db: Session = Depends(get_db),
        current_user = Depends(require_community_admin)
    ):
    return toggle_coordinator_status_service(
        coordinator_id=coordinator_id,
        db=db,
        current_user=current_user,
        request=request
    )


@router.get("/coordinators")
def fetch_coordinators(db : Session = Depends(get_db), current_user = Depends(require_community_admin)):
    return fetch_coordinators_service(db, current_user)

@router.post("/resend-coordinator-invite")
def resend_invite(email: str, db: Session = Depends(get_db), current_user=Depends(require_community_admin)):
    return resend_invite_service(email, db)

@router.get("/me")
def get_me(db : Session = Depends(get_db) ,current_user=Depends(require_community_admin)):
    return get_me_service(db, current_user)


@router.get("/coordinator-logs")
def fetch_coordinator_logs(
        db : Session = Depends(get_db), 
        coordinator_id : str = None,
        current_user = Depends(require_community_admin)
    ):
    return fetch_coordinator_logs_service(db, coordinator_id, current_user)


@router.get("/users")
def fetch_users(db : Session = Depends(get_db), current_user = Depends(require_community_admin)):
    return fetch_users_service(db, current_user)



@router.post("/create-event", response_model=EventResponse)
def create_event(
        payload : EventCreate,
        db: Session = Depends(get_db),
        current_user=Depends(require_community_admin),
        request: Request = None
    ):
    return create_event_service(payload, db, current_user, request)
@router.get("/get-events", response_model=EventResponse)
def get_events(
        db: Session = Depends(get_db),
        current_user=Depends(require_community_admin),
        request: Request = None
    ):
    return list_events_service(db, current_user, request)

@router.post("/events/{event_id}/poster")
def upload_event_poster(
        event_id: str,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user=Depends(require_community_admin),
        request: Request = None
    ):
    return upload_event_image_service(event_id, file, db, current_user, request)

@router.post("/events/{event_id}/images")
def upload_event_image(
        event_id: str,
        file: UploadFile = File(...),
        is_poster: bool = False,
        db: Session = Depends(get_db),
        current_user=Depends(require_community_admin),
        request: Request = None
    ):
    return upload_event_image_service(event_id, file, db, current_user, request, is_poster)

@router.get("/events/{event_id}/images")
def get_event_images(
        event_id: str,
        db: Session = Depends(get_db),
        current_user=Depends(require_community_admin)
    ):
    return get_event_images_service(event_id, db, current_user)

@router.put("/events/{event_id}/images/{image_id}/poster")
def set_event_poster(
        event_id: str,
        image_id: str,
        db: Session = Depends(get_db),
        current_user=Depends(require_community_admin),
        request: Request = None
    ):
    return set_event_poster_service(event_id, image_id, db, current_user, request)

@router.delete("/events/{event_id}/images/{image_id}")
def delete_event_image(
        event_id: str,
        image_id: str,
        db: Session = Depends(get_db),
        current_user=Depends(require_community_admin),
        request: Request = None
    ):
    return delete_event_image_service(event_id, image_id, db, current_user, request)


@router.post("/add-members")
def add_members(
        payload : MemberCreate,
        db : Session = Depends(get_db),
        current_user = Depends(require_community_admin),
        request: Request = None
    ):
    return add_member_service(payload, db, current_user, request)  

@router.get("/get-members")
def get_members(
        db : Session = Depends(get_db),
        current_user = Depends(require_community_admin)
    ):
    return get_members_service(db, current_user)


# Announcement Endpoints
@router.post("/create-announcement")
def create_announcement(
        payload: AnnouncementCreate,
        request: Request,
        db: Session = Depends(get_db),
        current_user = Depends(require_community_admin)
    ):
    return create_announcement_service(payload, db, current_user, request)


@router.get("/get-announcements")
def get_announcements(
        db: Session = Depends(get_db),
        current_user = Depends(require_community_admin)
    ):
    return list_announcements_service(db, current_user)


@router.post("/announcements/{announcement_id}/publish")
def publish_announcement(
        announcement_id: str,
        request: Request,
        db: Session = Depends(get_db),
        current_user = Depends(require_community_admin)
    ):
    return publish_announcement_service(announcement_id, db, current_user, request)


@router.delete("/announcements/{announcement_id}")
def delete_announcement(
        announcement_id: str,
        request: Request,
        db: Session = Depends(get_db),
        current_user = Depends(require_community_admin)
    ):
    return delete_announcement_service(announcement_id, db, current_user, request)