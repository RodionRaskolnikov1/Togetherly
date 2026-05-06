from typing import Optional, Literal
from database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from utils.auth_utils import get_current_user

from services.community_services import (
    get_communities_service,
    get_members_service,
    get_joined_communities,
    get_pending_communities,
    get_rejected_communities,
    get_community_notifications,
)

from services.feed_services import (
    get_suggested_profiles,
    send_connection_request,
    get_connection_requests,
    create_support_ticket_service,
    submit_feedback_service,
    set_favourites_service,
    get_my_connections,
    respond_to_connection_request,
    get_pending_requests,
    remove_connection
)

from utils.enums import (
    FamilyStatusEnum, FamilyTypeEnum,
    EmploymentStatusEnum
)

from schemas.settings_schema import SupportTicketCreate, AppFeedbackCreate, SetFavouritesRequest

from models import (
    User, ProfileFavourite
)


router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/communities")
def get_communities(
        city_id : Optional[str] = None,
        sub_caste_id : Optional[str] = None,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return get_communities_service(db, current_user, city_id, sub_caste_id)
    

@router.get("/community-members/{community_id}")
def get_community_members(
        community_id: str,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
    return get_members_service(db, current_user, community_id)


@router.get("/joined-communities")
def joined_communities(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return get_joined_communities(db, current_user)

@router.get("/pending-communities")
def pending_communities(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return get_pending_communities(db, current_user)


@router.get("/rejected-communities")
def rejected_communities(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return get_rejected_communities(db, current_user)

@router.get("/community-notifications")
def community_notifications(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return get_community_notifications(db, current_user)


@router.get("/profiles")
def get_profiles(
        min_age: int = None,
        max_age: int = None,
        min_height: int = None,
        max_height: int = None,
        min_income: int = None,
        max_income: int = None,
        marital_status: list[str] = Query(None),
        city_id : str = None,
        sub_caste_id: str = None,
        education_level: str = None,
        family_type : Optional[FamilyTypeEnum] = None,
        family_status : Optional[FamilyStatusEnum] = None,
        employment_status: Optional[EmploymentStatusEnum] = None,
        verified_only: bool = False,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return get_suggested_profiles (
        db=db,
        current_user=current_user,
        min_age=min_age,
        max_age=max_age,
        min_height=min_height,
        max_height=max_height,
        min_income=min_income,
        max_income=max_income,
        marital_status=marital_status,
        city_id=city_id,
        sub_caste_id=sub_caste_id,
        education_level=education_level,
        family_type=family_type,
        family_status=family_status,
        employment_status=employment_status,
        verified_only=verified_only
    )
    
    
@router.post("/connection-request")
def send_request(
        profile_id: str = Query(...),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return send_connection_request(db, profile_id, current_user)
 
 
@router.get("/connection-requests")
def get_requests(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return get_connection_requests(db, current_user)
 
    
@router.post("/connection-request/{connection_id}/respond")
def respond_to_request(
        connection_id: str,
        action: Literal["accept", "reject"],
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return respond_to_connection_request(db, connection_id, action, current_user)
 
 
@router.get("/connections")
def my_connections(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return get_my_connections(db, current_user)
 
@router.get("/pending-connections")
def pending_connections(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return get_pending_requests(db, current_user)
 
@router.delete("/connections/{connection_id}")
def delete_connection(
        connection_id: str,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return remove_connection(db, connection_id, current_user)




@router.put("/profile/favourites")
def set_favourites(
    body: SetFavouritesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return set_favourites_service(body.user_ids, db, current_user)


@router.get("/profile/favourites")
def get_favourites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    favourites = db.query(ProfileFavourite).filter(
        ProfileFavourite.user_id == current_user.id  # ✅ no profile query needed
    ).all()

    return {
        "count": len(favourites),
        "favourites": [f.favourite_user_id for f in favourites]
    }


@router.post("/support/contact")
def create_support_ticket(
        payload: SupportTicketCreate,
        background_tasks: BackgroundTasks, 
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
):
    return create_support_ticket_service(
        db,
        current_user,
        payload,
        background_tasks
    )


@router.post("/feedback")
def submit_feedback(
        payload: AppFeedbackCreate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return submit_feedback_service(db, current_user, payload, background_tasks)


