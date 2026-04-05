import uuid
from database import Base
from sqlalchemy import Column, String, ForeignKey, Enum as SqlEnum, DateTime, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class UserBlock(Base):
    __tablename__ = "user_blocks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    blocker_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    blocked_user_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


    
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_user_id", name="unique_user_block"),
        CheckConstraint("blocker_id <> blocked_user_id", name="no_self_block"),
    )
    
    
    blocker = relationship("User", foreign_keys=[blocker_id], back_populates="blocked_users")
    blocked = relationship("User", foreign_keys=[blocked_user_id], back_populates="blocked_by_users")
    