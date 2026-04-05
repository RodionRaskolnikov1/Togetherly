from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    priority: str = "normal"
    is_pinned: bool = False
    expires_at: Optional[datetime] = None

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    is_pinned: Optional[bool] = None
    expires_at: Optional[datetime] = None

class AnnouncementResponse(BaseModel):
    id: str
    title: str
    content: str
    priority: str
    status: str
    is_pinned: bool
    created_by: str
    published_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
