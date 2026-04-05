from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
import uuid
    
class Community(Base):
    __tablename__ = "communities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    city_id = Column(String(36), ForeignKey("cities.id"), nullable=False)
    religion_id = Column(String(36), ForeignKey("religions.id"), nullable=False)
    caste_id = Column(String(36), ForeignKey("castes.id"), nullable=False)
    sub_caste_id = Column(String(36), ForeignKey("sub_castes.id"), nullable=False)
    
    description = Column(String(1000), nullable=False)
    display_name = Column(String(150), nullable=False)

    
    __table_args__ = (
        UniqueConstraint(
            "city_id",
            "religion_id",
            "caste_id",
            "sub_caste_id"
        ),
    )



    city = relationship("City")

    religion = relationship("Religion")

    caste = relationship("Caste")

    sub_caste = relationship("SubCaste")
    
    events = relationship("Events", back_populates="community")

    announcements = relationship("Announcement", back_populates="community", cascade="all, delete-orphan")

    community_requests = relationship("CommunityRequest",back_populates="community",cascade="all, delete-orphan")
    
    verification_documents = relationship("VerificationDocuments",back_populates="community")
    
    coordinator = relationship("Coordinator", back_populates="community", uselist=False)
    
    community_admin = relationship("CommunityAdmin", back_populates="community", uselist=False)
    
    member = relationship("Member", back_populates="community")
    
    profiles = relationship("ProfileCommunity", back_populates="community", cascade="all, delete-orphan")