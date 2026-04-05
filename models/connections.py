from sqlalchemy import CheckConstraint, Column, String, DateTime, UniqueConstraint, func, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from database import Base
import uuid
from utils.enums import ConnectionRequestEnum


class ProfileConnections(Base):
    __tablename__ = "profile_connections"

    id = Column(String(36), primary_key=True,default=lambda: str(uuid.uuid4()))

    sender_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    receiver_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)

    status = Column(
        SqlEnum(ConnectionRequestEnum, name="connection_request_status"),
        nullable=False,
        server_default=ConnectionRequestEnum.pending.value 
    )

    created_at = Column(DateTime, server_default=func.now())
    responded_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("sender_id", "receiver_id"),
        CheckConstraint("sender_id != receiver_id"),
    )

    sender = relationship(
        "Profile",
        foreign_keys=[sender_id],
        back_populates="sent_connections"
    )

    receiver = relationship(    
        "Profile",
        foreign_keys=[receiver_id],
        back_populates="received_connections"
    )