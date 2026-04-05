from pydantic import BaseModel, Field, model_validator
from utils.enums import VisibilityEnum
from typing import Optional

from utils.enums import DietEnum

class VisibilityUpdate(BaseModel):
    visibility : VisibilityEnum


class SupportTicketCreate(BaseModel):
    subject: str = Field(..., min_length=3, max_length=255)
    message: str = Field(..., min_length=10, max_length=2000)
    

class AppFeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)  # 1 to 5 only
    message: str | None = Field(None, max_length=1000) 
    

class SetFavouritesRequest(BaseModel):
    user_ids: list[str]


class UserPreferenceCreate(BaseModel):
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    min_income: Optional[int] = None
    max_income: Optional[int] = None
    diet_preference: Optional[DietEnum] = None
    NRI: Optional[bool] = None
    
   
    @model_validator(mode="after")
    def validate_age_range(self):
        if self.min_age is not None and self.max_age is not None:
            if self.min_age > self.max_age:
                raise ValueError("min_age cannot be greater than max_age")
        return self
    
    @model_validator(mode="after")
    def validate_income_range(self):
        if self.min_income is not None and self.max_income is not None:
            if self.min_income > self.max_income:
                raise ValueError("min_income cannot be greater than max_income")
        return self
    
    @model_validator(mode="after")
    def max_two_filters(self):
        active = [
            f for f, v in {
                "age": self.min_age is not None or self.max_age is not None,
                "income": self.min_income is not None or self.max_income is not None,
                "diet": self.diet_preference is not None,
                "nri": self.NRI is True,
            }.items() if v
        ]
        
        if len(active) > 2:
            raise ValueError(
                f"Only 2 preference filters allowed at a time. You set: {active}"
            )
        return self
    