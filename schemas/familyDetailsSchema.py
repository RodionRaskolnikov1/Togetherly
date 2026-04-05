from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from utils.enums import (FamilyTypeEnum, FamilyStatusEnum, FamilyValuesEnum, ParentStatusEnum)

class FamilyDetailsCreate(BaseModel):
    family_type: Optional[FamilyTypeEnum] = None
    family_status: Optional[FamilyStatusEnum] = None
    family_values: Optional[FamilyValuesEnum] = None

    father_status: Optional[ParentStatusEnum] = None
    father_occupation: Optional[str] = None

    mother_status: Optional[ParentStatusEnum] = None
    mother_name: Optional[str] = None
    mother_occupation: Optional[str] = None

    number_of_family_members: Optional[int] = 0
    number_of_brothers: Optional[int] = 0
    number_of_sisters: Optional[int] = 0

    is_orphan: bool = False
    guardian_details: Optional[str] = None
    
    
    @field_validator("number_of_brothers", "number_of_sisters")
    @classmethod
    def validate_sibling_count(cls, v):
        if v is not None and v < 0:
            raise ValueError("Sibling count cannot be negative")
        return v
    
    
    @model_validator(mode="after")
    def validate_orphan_logic(self):
        if self.is_orphan:
            if self.father_status or self.mother_status:
                raise ValueError("Parent status not allowed if user is orphan")

            if not self.guardian_details:
                raise ValueError("Guardian details required if user is orphan")
        return self

    @model_validator(mode="after")
    def validate_parent_occupation(self):
        if self.father_status == ParentStatusEnum.deceased and self.father_occupation:
            raise ValueError("Father occupation not allowed if father is deceased")

        if self.mother_status == ParentStatusEnum.deceased and self.mother_occupation:
            raise ValueError("Mother occupation not allowed if mother is deceased")

        return self
    
    @model_validator(mode="after")
    def validate_family_count(self):
        total_children = (self.number_of_brothers or 0) + (self.number_of_sisters or 0)
        if self.number_of_family_members is not None and total_children > self.number_of_family_members:
            raise ValueError("Family members cannot be less than siblings count")
        return self

    
    
