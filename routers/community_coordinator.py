from fastapi import APIRouter, Depends, Request
from httpcore import request
from schemas.verificationDocumentsSchema import VerificationDocumentReview
from schemas.community_request_decision import CommunityRequestDecision

from services.coordinator_services import (
    get_coordinator_dashboard,
    get_coordinator_dashboard_stats,
    fetch_community_requests,
    decide_community_request,
    get_community_requests_service,
    get_members_service,
    get_member_details_service,
    get_coordinator_logs_service,
    get_coordinator_reports_service,
    get_coordinator_events_service,
    get_coordinator_event_detail_service,
    get_coordinator_announcements_service,
    get_coordinator_me_service
)

from services.review_verification_document_service import (
    get_pending_documents_for_coordinator,
    review_document_service,
    get_profile_documents_service,
    review_document_service

)

from schemas.dashboardSchema import CoordinatorUserDetailsResponse
from utils.auth_utils import require_community_coordinator
from database import get_db 
from sqlalchemy.orm import Session

router = APIRouter(prefix="/coordinator", tags=["coordinator"])



@router.get("/dashboard")
def coordinator_dashboard(db: Session = Depends(get_db), current_user = Depends(require_community_coordinator)):
    return get_coordinator_dashboard(db, current_user)

@router.get("/dashboard/stats")
def coordinator_dashboard_stats(db: Session = Depends(get_db), current_user = Depends(require_community_coordinator)):
    return get_coordinator_dashboard_stats(db, current_user)

@router.get("/logs")
def coordinator_logs(db: Session = Depends(get_db), current_user = Depends(require_community_coordinator)):
    return get_coordinator_logs_service(db, current_user)

@router.get("/reports")
def coordinator_reports(db: Session = Depends(get_db), current_user = Depends(require_community_coordinator)):
    return get_coordinator_reports_service(db, current_user)

@router.get("/community-requests")
def community_requests(
        request: Request,
        db: Session = Depends(get_db),
        current_user = Depends(require_community_coordinator),
        status: str = "pending"
    ):
    return fetch_community_requests(db, current_user, request, status)

@router.get("/community-requests/{request_id}", response_model=CoordinatorUserDetailsResponse)
def get_community_request(
        request: Request,
        request_id: str,
        db: Session = Depends(get_db),
        current_user = Depends(require_community_coordinator)
    ):
    return get_community_requests_service(request_id, db, current_user, request)

@router.post("/community-requests/{request_id}/decision")
def decide_request(request: Request, request_id: str, payload: CommunityRequestDecision, db: Session = Depends(get_db), current_user = Depends(require_community_coordinator)):
    return decide_community_request(
        request_id=request_id,
        action=payload.action,
        db=db,
        request=request,
        current_user=current_user
    )


@router.get("/documents/pending")
def get_pending_documents(request: Request, db: Session = Depends(get_db), current_user = Depends(require_community_coordinator)):
    return get_pending_documents_for_coordinator(db, current_user)

@router.post("/documents/{document_id}/review")
def review_document(
        request: Request,
        document_id: str,
        payload: VerificationDocumentReview,
        db: Session = Depends(get_db),
        current_user = Depends(require_community_coordinator)
    ):
    return review_document_service(
        request,
        document_id,
        payload.status,
        db,
        current_user,
        payload.rejection_reason,
        payload.coordinator_message
    )

@router.get("/profile/documents/{profile_id}")
def get_profile_documents(
        request: Request,
        profile_id: str,
        db: Session = Depends(get_db),
        current_user = Depends(require_community_coordinator)
    ):
    return get_profile_documents_service(profile_id, db, current_user, request)
    
    
@router.get("/members")
def get_members(db: Session = Depends(get_db), current_user = Depends(require_community_coordinator)):
    return get_members_service(db, current_user)

@router.get("/member-details/{user_id}", response_model=CoordinatorUserDetailsResponse)
def get_member_details(
        user_id: str,
        db: Session = Depends(get_db),
        current_user = Depends(require_community_coordinator)
    ):
    return get_member_details_service(user_id, db, current_user)



@router.get("/me")
def get_coordinator_me(db: Session = Depends(get_db), current_user = Depends(require_community_coordinator)):
    return get_coordinator_me_service(db, current_user)


@router.get("/events")
def get_coordinator_events(db: Session = Depends(get_db), current_user = Depends(require_community_coordinator)):
    return get_coordinator_events_service(db, current_user)


@router.get("/events/{event_id}")
def get_coordinator_event_detail(event_id: str, db: Session = Depends(get_db), current_user = Depends(require_community_coordinator)):
    return get_coordinator_event_detail_service(event_id, db, current_user)


@router.get("/announcements")
def get_coordinator_announcements(db: Session = Depends(get_db), current_user = Depends(require_community_coordinator)):
    return get_coordinator_announcements_service(db, current_user)