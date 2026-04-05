from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, String, CheckConstraint
from sqlalchemy.orm import relationship
import uuid
from database import Base

class ProfileFavourite(Base):
    __tablename__ = "profile_favourites"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    favourite_user_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "favourite_user_id", name="uq_profile_favourite"),
        CheckConstraint("user_id <> favourite_user_id", name="no_self_favourite"),
    )

    current_user = relationship("User", foreign_keys=[user_id], back_populates="favourite_users")
    favourite_user = relationship("User", foreign_keys=[favourite_user_id], back_populates="favourited_by_users")
