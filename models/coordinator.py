from database import Base
from sqlalchemy import DateTime, String, Column, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
import uuid

class Coordinator(Base):
    __tablename__ = "coordinators"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)   
    community_id = Column(String(36), ForeignKey('communities.id'), nullable=False)
    community_admin_id = Column(String(36), ForeignKey('community_admin.id'), nullable=False)
    
    is_active = Column(Boolean, nullable=False, server_default="true")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="coordinator")
    community = relationship("Community", back_populates="coordinator")
    community_admin = relationship("CommunityAdmin", back_populates="coordinator")
    
