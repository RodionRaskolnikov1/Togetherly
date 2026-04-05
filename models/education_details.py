import uuid
from database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship 
from sqlalchemy import Column, String, Float , Date, DateTime, CheckConstraint, ForeignKey, Integer, Text, Enum as SqlEnum
from utils.enums import EducationLevelEnum, PassingStatusEnum


class EducationDetails(Base):
    __tablename__ = "education_details"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey('profiles.id', ondelete="CASCADE"), nullable=False)
    
    level = Column(SqlEnum(EducationLevelEnum, name="education_level"), nullable=False) 
    status = Column(SqlEnum(PassingStatusEnum, name="passing_status"), nullable=False) 
    
    
    course_name = Column(String(100), nullable=True)
    institution_name = Column(String(150), nullable=True)
    board_name = Column(String(150), nullable=True)
    school_name = Column(String(150), nullable=True)
    university_name = Column(String(150), nullable=True)
    stream = Column(String(100), nullable=True)
    
    percentage_or_cgpa = Column(Float, nullable=True)
    passing_year = Column(Integer, nullable=True)
    last_class_completed = Column(Integer, nullable=True)

        
    profile = relationship("Profile", back_populates="education_details")