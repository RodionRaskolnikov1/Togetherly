from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from utils.enums import MaritalStatusEnum, ChildrenLivingWithEnum

class ProfileCreate(BaseModel):
    bio:  Optional[str] = None

    caste_id : str
    sub_caste_id : str
    religion_id : str

    marital_status: MaritalStatusEnum
    number_of_children: Optional[int] = 0
    children_living_with: Optional[ChildrenLivingWithEnum] = None

    @field_validator("number_of_children", mode="after")
    @classmethod
    def validate_children_count(cls, v, info):
        marital_status = info.data.get("marital_status")

        if marital_status == MaritalStatusEnum.never_married:
            if v and v > 0:
                raise ValueError("Never married users cannot have children")

        if v is not None and v < 0:
            raise ValueError("Number of children cannot be negative")

        return v
    
    @field_validator("children_living_with", mode="after")
    @classmethod
    def validate_children_living_with(cls, v, info):
        marital_status = info.data.get("marital_status")
        children = info.data.get("number_of_children", 0)

        if marital_status == MaritalStatusEnum.never_married and v is not None:
            raise ValueError("Children living details not allowed for never married users")

        if children == 0 and v is not None:
            raise ValueError("children_living_with not allowed when number_of_children is 0")

        return v
    

class ProfileResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    
    model_config = ConfigDict(from_attributes=True)

