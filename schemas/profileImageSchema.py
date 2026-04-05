from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProfileImageCreate(BaseModel):
    is_primary: Optional[bool] = False

class ProfileImageResponse(BaseModel):
    id: str
    profile_id: str
    image_url: str
    is_primary: bool
    created_at: str
    
    model_config = ConfigDict(from_attributes=True)
