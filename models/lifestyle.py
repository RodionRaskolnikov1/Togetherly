import uuid
from enum import Enum
from sqlalchemy import CheckConstraint, Column, String, ForeignKey, Integer, Text, Enum as SqlEnum
from sqlalchemy.orm import relationship
from database import Base
from utils.enums import (
    DietEnum, YesNoOccasionalEnum, 
    PhysicalStatusEnum, BloodGroupEnum,
    BodyTypeEnum
)

class Lifestyle(Base):
    __tablename__ = "lifestyles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    profile_id = Column(String(36),ForeignKey("profiles.id", ondelete="CASCADE"),nullable=False,unique=True)
    diet = Column(SqlEnum(DietEnum, name="diet_enum"), nullable=False)
    smoking = Column(SqlEnum(YesNoOccasionalEnum, name="smoking_enum"), nullable=False)
    drinking = Column(SqlEnum(YesNoOccasionalEnum, name="drinking_enum"), nullable=False)
    physical_status = Column(SqlEnum(PhysicalStatusEnum, name="physical_status_enum"), nullable=False)
    health_issues = Column(String(100), nullable=True)
    blood_group = Column(SqlEnum(BloodGroupEnum, name="blood_group_enum"), nullable=False)
    body_type = Column(SqlEnum(BodyTypeEnum, name="body_type_enum"), nullable=False)
    height = Column(Integer)
    weight = Column(Integer)

    profile = relationship("Profile", back_populates="lifestyle")
    
    __table_args__ = (
        CheckConstraint("height > 0"),
        CheckConstraint("weight > 0"),
    )
    

    