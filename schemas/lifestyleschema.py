from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional
from utils.enums import (
    DietEnum, YesNoOccasionalEnum,
    PhysicalStatusEnum, BloodGroupEnum,
    BodyTypeEnum
)

class LifestyleBase(BaseModel):
    diet: DietEnum
    smoking: YesNoOccasionalEnum
    drinking: YesNoOccasionalEnum
    physical_status: PhysicalStatusEnum
    health_issues: Optional[str] = None
    blood_group: BloodGroupEnum
    body_type : BodyTypeEnum
    height: int
    weight: int

class LifestyleCreate(LifestyleBase):
    pass


class LifestyleResponse(LifestyleBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
    
