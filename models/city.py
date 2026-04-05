from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
import uuid
class City(Base):
    __tablename__ = "cities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    state_id = Column(String(36), ForeignKey('states.id'), nullable=False)
    
    name = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)

    state = relationship("State", back_populates="cities")

    __table_args__ = (
        UniqueConstraint('state_id', 'name' , 'pincode'),
    )

    permanent_addresses = relationship("PermanentAddress", back_populates="city")    
    current_addresses = relationship("CurrentAddress", back_populates="city")
    work_addresses = relationship("WorkAddress", back_populates="city")
    
