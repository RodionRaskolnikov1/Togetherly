from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SqlEnum, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from database import Base
import uuid


from utils.enums import DietEnum

class UserPreference(Base):
    __tablename__ = "user_preference"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)    
    
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)
    
    min_income = Column(Integer, nullable=True)
    max_income = Column(Integer, nullable=True)
    
    diet_preference = Column(SqlEnum(DietEnum, name="diet_enum"), nullable=True)
    
    NRI = Column(Boolean, nullable=True, default=False, server_default="0")
    
    __table_args__ = (
        CheckConstraint("min_age IS NULL OR max_age IS NULL OR min_age <= max_age"),
        CheckConstraint("min_income IS NULL OR max_income IS NULL OR min_income <= max_income"),
        CheckConstraint("min_age IS NULL OR min_age >= 18"),
    )
    
    user = relationship("User",back_populates="user_preference")