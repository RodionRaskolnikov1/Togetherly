from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import date
from utils.enums import GenderEnum

class CoordinatorInvite(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    first_name: str
    father_name: str
    last_name: str
    dob: date
    gender: GenderEnum

    model_config = ConfigDict(from_attributes=True)


class CoordinatorCreate(BaseModel):
    user: CoordinatorInvite
    