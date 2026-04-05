from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
import uuid

class State(Base):
    __tablename__ = "states"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    country_id = Column(String(36), ForeignKey('countries.id'), nullable=False)
    
    name = Column(String(100), nullable=False)
   
    cities = relationship("City", back_populates="state")
    country = relationship("Country", back_populates="states")
    
    
    __table_args__ = (
        UniqueConstraint("country_id", "name"),
    )

    current_addresses = relationship("CurrentAddress", back_populates="state")
    permanent_addresses = relationship("PermanentAddress", back_populates="state")    
    work_addresses = relationship("WorkAddress", back_populates="state")
    
    
