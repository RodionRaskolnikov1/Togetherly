from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SqlEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from utils.enums import TicketStatusEnum    

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    subject = Column(String(255), nullable=False)
    message = Column(String, nullable=False)
    status = Column(SqlEnum(TicketStatusEnum), server_default=TicketStatusEnum.open.value)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  

    user = relationship("User", back_populates="support_tickets")