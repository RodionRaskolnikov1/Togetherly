from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from database import Base
import uuid

class Country(Base):
    __tablename__ = "countries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
   
   
    states = relationship("State", back_populates="country")
   
    current_addresses = relationship("CurrentAddress", back_populates="country")
    permanent_addresses = relationship("PermanentAddress", back_populates="country")    
    work_addresses = relationship("WorkAddress", back_populates="country")
    
    