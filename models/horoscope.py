import uuid
from database import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Time, Enum as SqlEnum
from sqlalchemy.orm import relationship
from utils.enums import ManglikStatusEnum

class Horoscope(Base):
    __tablename__ = "horoscopes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"),nullable=False,unique=True)
    
    time_of_birth = Column(Time, nullable=True)
    place_of_birth =  Column(String(255), nullable=False)
    rashi = Column(String(50), nullable=False)
    nakshatra = Column(String(50), nullable=False)
    
    manglik_status = Column(
        SqlEnum(ManglikStatusEnum, name="manglik_status"), 
        nullable=True, 
        server_default=ManglikStatusEnum.no.value
    )
    
    dosha_summary = Column(String(255), nullable=True)
        
    profile = relationship("Profile", back_populates="horoscope")
    