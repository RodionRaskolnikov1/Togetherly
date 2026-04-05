from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base
import uuid

class AppFeedback(Base):
    __tablename__ = "app_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    rating = Column(Integer, nullable=False)   
    message = Column(String(1000), nullable=True)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="app_feedback")