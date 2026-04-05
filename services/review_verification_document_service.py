from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.verification_document import VerificationDocuments
from models.coordinator import Coordinator
from models.user import User
from models.profile import Profile
from models.community import Community
from utils.enums import DocumentStatusEnum
from utils.logs import create_user_log

def get_pending_documents_for_coordinator(db: Session, current_user):
    """
    Get all pending verification documents for communities that the coordinator manages.
    """
    # Get communities that this coordinator manages
    community_ids = (
        db.query(Coordinator.community_id)
        .filter(Coordinator.user_id == current_user.id, Coordinator.is_active == True)
        .all()
    )
    community_ids = [row.community_id for row in community_ids]

    if not community_ids:
        return []

    # Get pending documents for those communities
    documents = (
        db.query(
            VerificationDocuments.id,
            VerificationDocuments.document_type,
            VerificationDocuments.file_url,
            VerificationDocuments.uploaded_at,
            User.first_name,
            User.last_name,
            Community.display_name.label("community_name"),
            Profile.id.label("profile_id")
        )
        .join(Profile, Profile.id == VerificationDocuments.profile_id)
        .join(User, User.id == Profile.user_id)
        .join(Community, Community.id == VerificationDocuments.community_id)
        .filter(
            VerificationDocuments.community_id.in_(community_ids),
            VerificationDocuments.status == DocumentStatusEnum.pending
        )
        .all()
    )

    return [
        {
            "document_id": doc.id,
            "document_type": doc.document_type,
            "file_url": doc.file_url,
            "uploaded_at": doc.uploaded_at,
            "user_name": f"{doc.first_name} {doc.last_name}",
            "community_name": doc.community_name,
            "profile_id": doc.profile_id
        }
        for doc in documents
    ]

def review_document_service(request ,document_id: str, status: str, db: Session, current_user, rejection_reason: str = None, coordinator_message: str = None):
    """
    Allow coordinator to approve or reject a verification document.
    """
    if status not in ["approved", "rejected"]:
        raise HTTPException(400, "Invalid status. Must be 'approved' or 'rejected'")

    # Find the document
    document = db.query(VerificationDocuments).filter_by(id=document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")

    # Check if coordinator is authorized for this document's community
    coordinator_check = db.query(Coordinator).filter_by(
        user_id=current_user.id,
        community_id=document.community_id,
        is_active=True
    ).first()

    if not coordinator_check:
        raise HTTPException(403, "Not authorized to review this document")

    if document.status != DocumentStatusEnum.pending:
        raise HTTPException(400, "Document has already been reviewed")

    try:
        document.status = DocumentStatusEnum(status)
        document.reviewed_at = datetime.utcnow()
        document.reviewed_by = current_user.id

        if status == "rejected":
            if not rejection_reason:
                raise HTTPException(400, "Rejection reason is required for rejected documents")
            document.rejection_reason = rejection_reason

        # Save coordinator message if provided
        if coordinator_message:
            document.coordinator_message = coordinator_message

        db.commit()

        # Create log entry - get user_id from profile
        profile = db.query(Profile).filter_by(id=document.profile_id).first()
        if profile:
            create_user_log(
                db=db,
                user_id=profile.user_id,
                action=f"Document {status}",
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to review document: {str(e)}")

    return {"message": f"Document {status} successfully"}


def get_profile_documents_service(profile_id: str, db: Session, current_user : User, request):
    
    profile = db.query(Profile).filter_by(id=profile_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")

    documents = db.query(VerificationDocuments).filter_by(profile_id=profile_id).all()

    return {"documents": documents}
