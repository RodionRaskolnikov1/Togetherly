import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from utils.enums import RegistrationStatusEnum  

class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    event_id = Column(String(36), ForeignKey('events.id', ondelete="CASCADE"), nullable=False)
    member_id = Column(String(36), ForeignKey('members.id', ondelete="CASCADE"), nullable=False)

    status = Column(
        SqlEnum(RegistrationStatusEnum, name="registration_status"),
        nullable=False,
        default=RegistrationStatusEnum.registered
    )

    registered_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('event_id', 'member_id', name='uq_event_member'),
    )

    event = relationship("Events", back_populates="registrations")
    member = relationship("Member", back_populates="registrations")