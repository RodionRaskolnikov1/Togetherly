from fastapi import APIRouter, Depends
from utils.auth_utils import get_current_user
from sqlalchemy.orm import Session
from database import get_db

from utils.enums import (
    VisibilityEnum
)

from models import (
    User, UserSettings
)

from schemas.settings_schema import (
    VisibilityUpdate,
    UserPreferenceCreate
)

from services.feed_services import (
    get_blocked_users,
    block_user_service,
    unblock_user_service,
    get_or_create_preference,    
    update_preference
)

router = APIRouter(prefix="/settings", tags=["settings"])

@router.put("/visibility")
def change_visibility(
        payload : VisibilityUpdate, 
        db : Session = Depends(get_db) , 
        current_user=Depends(get_current_user)
    ):
        
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if not settings:
        settings = UserSettings(
            user_id=current_user.id,
            visibility=payload.visibility
        )
        db.add(settings)
        
    else:
        settings.visibility = payload.visibility
    
    db.commit()
    db.refresh(settings)
    return {"visibility" : settings.visibility}
    
    
@router.get("/visibility")
def get_visibility(db : Session = Depends(get_db) , current_user=Depends(get_current_user)):
    
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        return {"visibility": VisibilityEnum.public}

    return {"visibility": settings.visibility}



@router.get("/blocked")
def get_blocked(db : Session = Depends(get_db) , current_user=Depends(get_current_user)):
    return get_blocked_users(db, current_user)
    
    
@router.post("/block/{user_id}")
def block_user(
        user_id: str,
        db : Session = Depends(get_db), 
        current_user=Depends(get_current_user),
    ):
    return block_user_service(db, current_user, user_id)
    
@router.delete("/block/{user_id}")
def unblock_user(user_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):    
    return unblock_user_service(db, current_user, user_id)


@router.get("/preference")
def get_preferences(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return get_or_create_preference(db, current_user)


@router.put("/update-preference", )
def set_preferences(
    data: UserPreferenceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return update_preference(db, current_user, data)


# @router.put("/privacy")
# @router.get("/privacy")

# @router.put("/notification")
# @router.get("/notification")




