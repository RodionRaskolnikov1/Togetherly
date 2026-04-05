import uuid
from sqlalchemy import Boolean, Column, String, Date, DateTime, text, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from utils.enums import EventStatusEnum
from sqlalchemy.sql import func
from database import Base

class Events(Base):
    __tablename__ = "events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    community_id = Column(
        String(36), 
        ForeignKey('communities.id', ondelete="CASCADE"), 
        nullable=False
    )

    title = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    location = Column(String(100), nullable=False)  
    
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    
    status = Column(SqlEnum(EventStatusEnum, name="event_status"), nullable=False)
    is_published = Column(Boolean, nullable=False, server_default=text("false"))

    poster_image_url = Column(String(500), nullable=True)
    poster_public_id = Column(String(255), nullable=True)
        
    created_by = Column(
        String(36), 
        ForeignKey('community_admin.id'),
        nullable=False
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    community = relationship("Community", back_populates="events")
    community_admin = relationship("CommunityAdmin", back_populates="events")
    event_images = relationship("EventImage", back_populates="event", cascade="all, delete-orphan")
    