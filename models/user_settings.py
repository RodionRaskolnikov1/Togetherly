from database import Base
from sqlalchemy import Column, String, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship

from utils.enums import VisibilityEnum

import uuid

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)    
        
    visibility = Column(SqlEnum(VisibilityEnum, name="visibility_enum"), nullable=False, server_default=VisibilityEnum.public.value)    
            
    user = relationship("User", back_populates="settings")
    
    
    
    
    