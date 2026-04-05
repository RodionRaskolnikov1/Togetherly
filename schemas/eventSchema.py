from pydantic import BaseModel, model_validator
from datetime import datetime
from utils.enums import EventStatusEnum

class EventCreate(BaseModel):
    title : str
    description : str
    location : str
    start_datetime : datetime
    end_datetime : datetime
    poster_image_url : str | None = None
    
    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_datetime <= self.start_datetime:
            raise ValueError("end_datetime must be after start_datetime")
        return self
    
class Event(BaseModel):
    id : str
    title : str
    description : str
    location : str
    start_datetime : datetime
    end_datetime : datetime
    status : EventStatusEnum
    is_published : bool
    poster_image_url : str | None = None

class EventResponse(BaseModel):
    events: list[Event]