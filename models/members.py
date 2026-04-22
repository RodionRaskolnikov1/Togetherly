import uuid
from database import Base
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

class Member(Base):
    __tablename__ = "members"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    community_id = Column(String(36), ForeignKey('communities.id', ondelete="CASCADE"), nullable=False)
    created_by = Column(String(36), ForeignKey('community_admin.id'), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'community_id', name='uq_user_community'),
    )
    
    user = relationship("User", back_populates="member")
    
    community = relationship("Community", back_populates="member")
    
    community_admin = relationship("CommunityAdmin", back_populates="member")
    
    registrations = relationship("EventRegistration", back_populates="member", cascade="all, delete-orphan")