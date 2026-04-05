import uuid
from sqlalchemy import Column, String, ForeignKey, Integer, Enum as SqlEnum
from sqlalchemy.orm import relationship 
from utils.enums import EmploymentStatusEnum
from database import Base

class ProfessionDetails(Base):
    __tablename__ = "profession_details"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey('profiles.id', ondelete="CASCADE"), nullable=False, unique=True)
    
    employment_status = Column(SqlEnum(EmploymentStatusEnum, name="employment_status_enum"), nullable=False)
    
    job_title = Column(String(255), nullable=True)
    organization_name = Column(String(255), nullable=True)
    
    annual_income = Column(Integer, nullable=True)
    start_year = Column(Integer, nullable=True)
    
    description = Column(String(1000), nullable=True)
            
            
    profile = relationship("Profile", back_populates="profession_details")
    work_address = relationship("WorkAddress", back_populates="profession", uselist=False, cascade="all, delete-orphan")