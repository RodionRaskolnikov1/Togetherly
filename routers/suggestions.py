from fastapi import APIRouter, Depends
from database import get_db
from sqlalchemy.orm import Session
from utils.auth_utils import get_current_user_with_details
from utils.enums import VisibilityEnum

from models import (
    User, Profile, 
    ProfileCommunity, Community,
    UserSettings, BlockedUser
)

from schemas.suggestionSchema import CommunitySuggestionUser

router = APIRouter(prefix="/suggestions", tags=["suggestions"])

@router.get("/community", response_model=list[CommunitySuggestionUser])
def get_community_suggestions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_with_details)
):
    community_ids = [
        pc.community_id
        for pc in current_user.profile.communities
    ]

    if not community_ids:
        return []


    users = (
        db.query(User)
        .join(Profile, Profile.user_id == User.id)
        .join(ProfileCommunity, ProfileCommunity.profile_id == Profile.id)
        .filter(ProfileCommunity.community_id.in_(community_ids))
        .filter(User.id != current_user.id)
        .filter(
            ~User.id.in_(
                db.query(BlockedUser.blocked_id)
                .filter(BlockedUser.blocker_id == current_user.id)
            ),
            ~User.id.in_(
                db.query(BlockedUser.blocker_id)
                .filter(BlockedUser.blocked_id == current_user.id)
            )
        )
        .distinct()
        .all()
    )

    return users

@router.get("/cities")
def get_city_suggestions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_with_details)
):

    users = (
        db.query(User)
        .join(Profile, Profile.user_id == User.id)
        .join(ProfileCommunity, ProfileCommunity.profile_id == Profile.id)
        .join(Community, Community.id == ProfileCommunity.community_id)
        .join(UserSettings, UserSettings.user_id == User.id)
        .filter(Community.city_id == current_user.profile.city_id)
        .filter(UserSettings.visibility == VisibilityEnum.public)
        .filter(User.id != current_user.id)
        .filter(
            ~User.id.in_(
                db.query(BlockedUser.blocked_id)
                .filter(BlockedUser.blocker_id == current_user.id)
            ),
            ~User.id.in_(
                db.query(BlockedUser.blocker_id)
                .filter(BlockedUser.blocked_id == current_user.id)
            )
        )
        .distinct()
        .all()
    )

    return users