from database import Base
from sqlalchemy import DateTime, String, Column, ForeignKey, func, Text
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SqlEnum
from utils.enums import CommunityRequestStatusEnum

import uuid

class CommunityRequest(Base):
    __tablename__ = "community_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    profile_id = Column(
        String(36), 
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    community_id = Column(
        String(36),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    
    status = Column(SqlEnum(CommunityRequestStatusEnum, name="community_request_enum"), server_default=CommunityRequestStatusEnum.pending.value)
    
    
    requested_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    reviewed_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    rejection_reason = Column(Text, nullable=True)
    
    
    profile = relationship("Profile", back_populates="community_requests")
    community = relationship("Community", back_populates="community_requests")