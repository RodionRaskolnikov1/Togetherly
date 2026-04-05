from database import Base
from sqlalchemy import Boolean, Column, DateTime, String, Integer, ForeignKey, Enum as SqlEnum, Text, func
from sqlalchemy.orm import relationship
from utils.enums import FamilyTypeEnum, FamilyStatusEnum, FamilyValuesEnum, ParentStatusEnum
import uuid

class FamilyDetails(Base):
    __tablename__ = "family_details" 
   
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey('profiles.id', ondelete="CASCADE"), nullable=False, unique=True)
    
    family_type = Column(SqlEnum(FamilyTypeEnum), nullable=True)
    family_status = Column(SqlEnum(FamilyStatusEnum), nullable=True)
    family_values = Column(SqlEnum(FamilyValuesEnum), nullable=True)

    father_status = Column(SqlEnum(ParentStatusEnum), nullable=True)
    father_occupation = Column(String(100), nullable=True)
    
    mother_status = Column(SqlEnum(ParentStatusEnum), nullable=True)
    mother_name = Column(String(100), nullable=True)
    mother_occupation = Column(String(100), nullable=True)
    
    number_of_family_members = Column(Integer, nullable=True)
    number_of_brothers = Column(Integer, nullable=True)
    number_of_sisters = Column(Integer, nullable=True)

    guardian_details = Column(Text, nullable=True)
    
    is_orphan = Column(Boolean, nullable=False, server_default="false")
    
    created_at = Column(DateTime, server_default=func.now())
    
    
    profile = relationship("Profile", back_populates="family_details")