from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
import uuid

class Caste(Base):
    __tablename__ = "castes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    religion_id = Column(String(36), ForeignKey("religions.id"), nullable=False)
    name = Column(String(100), nullable=False)

    religion = relationship("Religion", back_populates="castes")
    sub_castes = relationship("SubCaste", back_populates="caste")

    __table_args__ = (
        UniqueConstraint("religion_id", "name"),
    )
    
    profile = relationship("Profile", back_populates="caste")