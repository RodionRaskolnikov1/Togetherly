from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
import uuid

class SubCaste(Base):
    __tablename__ = "sub_castes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    caste_id = Column(String(36), ForeignKey("castes.id"), nullable=False)
    name = Column(String(100), nullable=False)

    caste = relationship("Caste", back_populates="sub_castes")

    __table_args__ = (
        UniqueConstraint("caste_id", "name"),
    )

    profile = relationship("Profile", back_populates="sub_caste")