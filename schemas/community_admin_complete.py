from pydantic import BaseModel, EmailStr, model_validator, field_validator
from schemas.userSchema import UserRegister
from typing import Optional
from utils.enums import GenderEnum
from datetime import date

class CommunityAdminUserCreate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: str
    father_name: Optional[str] = None
    last_name: str
    dob: date
    gender: GenderEnum


    @field_validator("email", mode="before")
    def empty_email_to_none(cls, v):
        if v == "":
            return None
        return v
    
    @model_validator(mode="after")
    def require_email_or_phone(cls, values):
        if not values.email and not values.phone:
            raise ValueError("Either email or phone must be provided")
        return values
    
    
class CommunityAdminComplete(BaseModel):
    user: CommunityAdminUserCreate
    community_id: str