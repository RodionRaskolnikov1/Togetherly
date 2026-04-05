import uuid
from sqlalchemy import Column, String, DateTime, CheckConstraint, ForeignKey, Integer, Text, Enum as SqlEnum
from sqlalchemy.orm import relationship 
from sqlalchemy.sql import func
from database import Base
from utils.enums import ProfileStageEnum, MaritalStatusEnum, ChildrenLivingWithEnum

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)    

    bio = Column(Text, nullable=True)
    
    caste_id = Column(String(36), ForeignKey("castes.id"), nullable=False)
    sub_caste_id = Column(String(36), ForeignKey("sub_castes.id"), nullable=False)
    religion_id = Column(String(36), ForeignKey("religions.id"), nullable=False)
    
    marital_status = Column(SqlEnum(MaritalStatusEnum, name="marital_status_enum"), nullable=False, server_default=MaritalStatusEnum.never_married.value)
    
    number_of_children = Column(Integer, CheckConstraint('number_of_children >= 0'), nullable=False, server_default="0")
    children_living_with  = Column(SqlEnum(ChildrenLivingWithEnum, name ="children_living_with_enum"), nullable=True)
    
    profile_stage = Column(SqlEnum(ProfileStageEnum, name="profile_stage_enum"), nullable=False,server_default=ProfileStageEnum.pending.value)
        
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())




    
    caste = relationship("Caste", back_populates="profile")
    
    sub_caste = relationship("SubCaste", back_populates="profile")
    
    religion = relationship("Religion", back_populates="profile")  
    
    user = relationship("User",back_populates="profile",foreign_keys=[user_id])
    
    communities = relationship("ProfileCommunity", back_populates="profile",cascade="all, delete-orphan")
    
    horoscope = relationship("Horoscope", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    
    family_details = relationship("FamilyDetails", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    
    education_details = relationship("EducationDetails",  back_populates="profile", cascade="all, delete-orphan")
    
    profession_details = relationship("ProfessionDetails", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    
    lifestyle = relationship("Lifestyle",back_populates="profile",uselist=False, cascade="all, delete-orphan")
    
    community_requests = relationship("CommunityRequest",back_populates="profile",cascade="all, delete-orphan")
    
    verification_documents = relationship("VerificationDocuments", back_populates="profile",cascade="all, delete-orphan")

    current_address = relationship("CurrentAddress", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    
    permanent_address = relationship("PermanentAddress", back_populates="profile", uselist=False, cascade="all, delete-orphan") 
    
    profile_images = relationship("ProfileImage", back_populates="profile", cascade="all, delete-orphan")

    sent_connections = relationship(
        "ProfileConnections",
        foreign_keys="ProfileConnections.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan"
    )

    received_connections = relationship(
        "ProfileConnections",
        foreign_keys="ProfileConnections.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan"
    )
    