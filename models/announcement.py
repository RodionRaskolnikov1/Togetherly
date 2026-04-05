import uuid
from sqlalchemy import Boolean, Column, String, DateTime, text, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

from utils.enums import AnnouncementPriority, AnnouncementStatus


class Announcement(Base):
    __tablename__ = "announcements"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    community_id = Column(
        String(36), 
        ForeignKey('communities.id', ondelete="CASCADE"), 
        nullable=False
    )

    title = Column(String(200), nullable=False)
    content = Column(String(5000), nullable=False)
    
    priority = Column(
        SqlEnum(AnnouncementPriority, name="announcement_priority"), 
        nullable=False, 
        server_default="normal"
    )
    
    status = Column(
        SqlEnum(AnnouncementStatus, name="announcement_status"), 
        nullable=False, 
        server_default="draft"
    )
    
    is_pinned = Column(Boolean, nullable=False, server_default=text("false"))
    
    created_by = Column(
        String(36), 
        ForeignKey('community_admin.id'),
        nullable=False
    )
    
    published_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    community = relationship("Community", back_populates="announcements")
    community_admin = relationship("CommunityAdmin", back_populates="announcements")
