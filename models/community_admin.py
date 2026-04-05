from database import Base
from sqlalchemy import Column, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
import uuid

class CommunityAdmin(Base):
    __tablename__ = "community_admin"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)
    community_id = Column(String(36), ForeignKey('communities.id', ondelete="CASCADE"), nullable=False, unique=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    
    
    
    user = relationship("User", back_populates="community_admin")
    
    community = relationship("Community", back_populates="community_admin")
    
    coordinator = relationship("Coordinator", back_populates="community_admin", cascade="all, delete-orphan")
    
    events = relationship("Events", back_populates="community_admin")

    announcements = relationship("Announcement", back_populates="community_admin", cascade="all, delete-orphan")

    member = relationship("Member", back_populates="community_admin")