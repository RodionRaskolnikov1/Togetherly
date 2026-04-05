import uuid
from database import Base
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,   
    ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from utils.enums import DocumentStatusEnum
from sqlalchemy import Enum as SqlEnum

class VerificationDocuments(Base):
    __tablename__ = "verification_documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    community_id = Column(
        String(36), 
        ForeignKey("communities.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    
    document_type = Column(String(50), nullable=False)
    
    file_url = Column(Text, nullable=False)
    public_id = Column(String(255), nullable=False)
    
    status = Column(
        SqlEnum(DocumentStatusEnum),
        server_default=DocumentStatusEnum.pending.value
    )

    
    rejection_reason = Column(Text, nullable=True)

    coordinator_message = Column(Text, nullable=True)

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    reviewed_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    profile = relationship("Profile", back_populates="verification_documents")
    community = relationship("Community", back_populates="verification_documents")