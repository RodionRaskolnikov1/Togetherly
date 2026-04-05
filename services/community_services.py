from datetime import date, datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from sqlalchemy import func

from models import (
    Profile, Community, CommunityRequest,
    PermanentAddress, City, ProfileCommunity
)

from utils.enums import GenderEnum, CommunityRequestStatusEnum
from utils.logs import create_user_log



def create_community_request(payload, db: Session, current_user):
    
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id  
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    community = db.query(Community).filter(
        Community.id == payload.community_id
    ).first()
    
    if not community:
        raise HTTPException(status_code=400, detail="Invalid community")
    
    existing = db.query(CommunityRequest).filter(
        CommunityRequest.profile_id == profile.id,
        CommunityRequest.community_id == community.id,
        CommunityRequest.status == CommunityRequestStatusEnum.pending
    ).first()
    
    if existing:
        raise HTTPException(
            400,
            "Community request already submitted"
        )
        
    request_entry = CommunityRequest(
        profile_id=profile.id,
        community_id=community.id,
        status="pending"
    )

    db.add(request_entry)
    
    profile.profile_stage = "submitted"

    db.commit()

    create_user_log(
        db=db,
        user_id=current_user.id,
        action="COMMUNITY_REQUEST_SUBMITTED"
    )

    return {
        "message": "Community request submitted successfully",
        "request_id": request_entry.id,
        "next_step": "Upload verification documents"
    }
    
    
def get_communities_service(db: Session, current_user, city_id = None, sub_caste_id = None):
    
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    permanent_address = db.query(PermanentAddress).filter(
        PermanentAddress.profile_id == profile.id   
    ).first()

    if not permanent_address:
        raise HTTPException(status_code=404, detail="Permanent address not found")
    
    if not permanent_address.state_id:
        raise HTTPException(status_code=400, detail="Invalid state configuration")
    
    user_state_id = permanent_address.state_id
    
    query = db.query(Community).join(
        City, Community.city_id == City.id
    ).filter(
        Community.caste_id == profile.caste_id,
        City.state_id == user_state_id,
    )
    
    if city_id:
        query = query.filter(Community.city_id == city_id)
    
    if sub_caste_id:
        query = query.filter(Community.sub_caste_id == sub_caste_id)
    
    communities = query.all()
    final = []
    community_ids = [com.id for com in communities]

    requests = db.query(CommunityRequest).filter(
        CommunityRequest.profile_id == profile.id,
        CommunityRequest.community_id.in_(community_ids)
    ).all()

    request_map = {req.community_id: req.status for req in requests}
        
    for com in communities:        
        final.append({
            "community": com,
            "status" : request_map.get(com.id)
        })  

    return final


def get_members_service(db: Session, current_user, community_id):
    
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    check = db.query(Community).filter(
        Community.id == community_id
    ).first()
    
    if not check:
        raise HTTPException(status_code=404, detail="Community not found")
    
    membership = db.query(ProfileCommunity).filter(
        ProfileCommunity.profile_id == profile.id,
        ProfileCommunity.community_id == community_id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this community")
    
    members = db.query(Profile).join(
        ProfileCommunity,
        Profile.id == ProfileCommunity.profile_id
    ).filter(
        ProfileCommunity.community_id == community_id,
    ).all()
    
    return {
        "member_count" : len(members),
        "members" : members
    }


def get_joined_communities(db : Session, current_user):
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    joined_communities = (
        db.query(Community)
        .join(ProfileCommunity, ProfileCommunity.community_id == Community.id)
        .filter(ProfileCommunity.profile_id == profile.id)
        .all()
    )
        
    return joined_communities


def get_pending_communities(db: Session, current_user):
    
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    pending_communities = (
        db.query(CommunityRequest)
        .filter(CommunityRequest.profile_id == profile.id)
        .filter(CommunityRequest.status == "pending")
        .all()
    )
    
    return pending_communities


def get_rejected_communities(db : Session, current_user):

    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    rejected_communities = (
        db.query(CommunityRequest)
        .filter(CommunityRequest.profile_id == profile.id)
        .filter(CommunityRequest.status == "rejected")
        .all()
    )
    
    return rejected_communities

def get_community_notifications(db: Session, current_user):
    
    current_time = datetime.now() - timedelta(days=1)
    
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    notifications = (
        db.query(CommunityRequest)
        .filter(CommunityRequest.profile_id == profile.id)
        .filter(CommunityRequest.status.in_(["approved", "rejected"]))
        .filter(CommunityRequest.reviewed_at >= current_time)
        .all()
    )
    
    return notifications