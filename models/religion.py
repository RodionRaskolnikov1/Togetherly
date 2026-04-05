from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base
import uuid

class Religion(Base):
    __tablename__ = "religions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)

    castes = relationship("Caste", back_populates="religion")
    profile = relationship("Profile", back_populates="religion")
    