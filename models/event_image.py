import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class EventImage(Base):
    __tablename__ = "event_images"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey('events.id', ondelete="CASCADE"), nullable=False)
    
    image_url = Column(String(500), nullable=False)
    public_id = Column(String(255), nullable=True)  # For cloudinary/storage management
    
    is_poster = Column(Boolean, nullable=False, server_default="false")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    event = relationship("Events", back_populates="event_images")
