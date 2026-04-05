from sqlalchemy import Column, Integer, String
from database import Base
import uuid

class University(Base):
    __tablename__ = "universities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    university_name = Column(String(255), nullable=False)
    college_name = Column(String(100), nullable=False)
    state_name = Column(String(100), nullable=True)
    college_type = Column(String(100), nullable=True)
    district_name = Column(String(100), nullable=True)