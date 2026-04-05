import uuid
from database import Base
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class UserLogs(Base):
    __tablename__ = "user_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    
    action = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="userlogs")
    
class AdminLogs(Base):
    __tablename__ = "admin_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    admin_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    
    action = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="admin_logs")

class CoordinatorLogs(Base):
    __tablename__ = "coordinator_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    coordinator_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    action = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="coordinator_logs")    

class SuperAdminLogs(Base):
    __tablename__ = "super_admin_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    super_admin_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    
    action = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="super_admin_logs")