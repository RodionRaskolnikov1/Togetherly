from database import Base
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid

class ProfileCommunity(Base):
    __tablename__ = "profile_communities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE") , nullable=False)
    community_id = Column(String(36), ForeignKey("communities.id", ondelete="CASCADE"), nullable=False)
    
    joined_at = Column(DateTime, server_default=func.now())
    verified_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)    
    verified_at = Column(DateTime)

    __table_args__ = (UniqueConstraint("profile_id", "community_id"),)
    
    
    
    
    
    profile = relationship("Profile", back_populates="communities")
    community = relationship("Community", back_populates="profiles")