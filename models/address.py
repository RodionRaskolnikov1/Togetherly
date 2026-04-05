import uuid
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, ForeignKey

class CurrentAddress(Base):
    __tablename__ = 'current_addresses'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey('profiles.id', ondelete="CASCADE"), nullable=False, unique=True)
    street = Column(String(100), nullable=False)
    area = Column(String(100), nullable=True)
    city_id = Column(String(36), ForeignKey("cities.id"), nullable=False)
    state_id = Column(String(36), ForeignKey("states.id"), nullable=False)
    pin_code = Column(String(20), nullable=False)
    country_id = Column(String(36), ForeignKey('countries.id'), nullable=False)
    
    profile = relationship("Profile", back_populates="current_address")
    city = relationship("City", back_populates="current_addresses")
    state = relationship("State", back_populates="current_addresses")
    country = relationship("Country", back_populates="current_addresses")

class PermanentAddress(Base):   
    __tablename__ = 'permanent_addresses'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey('profiles.id', ondelete="CASCADE"), nullable=False, unique=True)
    street = Column(String(100), nullable=False)
    area = Column(String(100), nullable=True)
    city_id = Column(String(36), ForeignKey("cities.id"), nullable=False)
    state_id = Column(String(36), ForeignKey("states.id"), nullable=False)
    pin_code = Column(String(20), nullable=False)
    country_id = Column(String(36), ForeignKey('countries.id'), nullable=False)
    
    profile = relationship("Profile", back_populates="permanent_address")
    city = relationship("City", back_populates="permanent_addresses")
    state = relationship("State", back_populates="permanent_addresses")
    country = relationship("Country", back_populates="permanent_addresses")
    
    
class WorkAddress(Base):
    __tablename__ = 'work_addresses'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profession_id = Column(
        String(36),
        ForeignKey("profession_details.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    
    city_id = Column(String(36), ForeignKey("cities.id"), nullable=False)
    state_id = Column(String(36), ForeignKey("states.id"), nullable=False)
    pin_code = Column(String(20), nullable=False)
    country_id = Column(String(36), ForeignKey('countries.id'), nullable=False)

    profession = relationship("ProfessionDetails", back_populates="work_address")
    city = relationship("City", back_populates="work_addresses")
    state = relationship("State", back_populates="work_addresses")
    country = relationship("Country", back_populates="work_addresses")
    