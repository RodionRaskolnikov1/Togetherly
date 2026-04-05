import uuid
from sqlalchemy import Boolean, Column, String, Date, DateTime, text, CheckConstraint
from sqlalchemy.orm import relationship 
from sqlalchemy.sql import func
from database import Base
from sqlalchemy import Enum as SqlEnum
from utils.enums import GenderEnum, RoleEnum, AccountStatusEnum


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    email = Column(String(200), unique=True, nullable=True)
    phone = Column(String(20), unique=True, nullable=True)
    
    email_verified = Column(Boolean, nullable=False, server_default=text("false"))
    phone_verified = Column(Boolean, nullable=False, server_default=text("false"))


    password_hash = Column(String(255), nullable=False) 

    first_name = Column(String(100), nullable=False)
    father_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=True)
    
    gender = Column(SqlEnum(GenderEnum, name="gender_enum"), nullable=False)
    role = Column(SqlEnum(RoleEnum, name="role_enum"), nullable=False, server_default=RoleEnum.user.value)
    account_status = Column(SqlEnum(AccountStatusEnum, name="account_status_enum"), nullable=False, server_default=AccountStatusEnum.pending.value)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
   
    __table_args__ = (
        CheckConstraint("email IS NOT NULL OR phone IS NOT NULL", name="require_email_or_phone"),
    )
    
    
    invites = relationship("Invite", back_populates="user", cascade="all, delete-orphan")
    
    member = relationship("Member", back_populates="user")

    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")

    community_admin = relationship("CommunityAdmin", back_populates="user", uselist=False)

    coordinator = relationship("Coordinator",back_populates="user",uselist=False)

    profile = relationship("Profile", back_populates="user", uselist=False, foreign_keys="Profile.user_id", cascade="all, delete-orphan")

    userlogs = relationship("UserLogs", back_populates="user", cascade="all, delete-orphan")
    
    admin_logs = relationship("AdminLogs", back_populates="user", cascade="all, delete-orphan")
    
    coordinator_logs = relationship("CoordinatorLogs", back_populates="user", cascade="all, delete-orphan")
    
    super_admin_logs = relationship("SuperAdminLogs", back_populates="user", cascade="all, delete-orphan")
    
    settings = relationship("UserSettings", back_populates="user", uselist=False, foreign_keys="UserSettings.user_id", cascade="all, delete-orphan")
    
    user_images = relationship("UserImage", back_populates="user", cascade="all, delete-orphan")
    
    blocked_users = relationship(
        "UserBlock",
        foreign_keys="UserBlock.blocker_id",
        back_populates="blocker"
    )

    blocked_by_users = relationship(
        "UserBlock",
        foreign_keys="UserBlock.blocked_user_id",
        back_populates="blocked"
    )
    
    support_tickets = relationship("SupportTicket", back_populates="user")
    
    app_feedback = relationship("AppFeedback", back_populates="user")
    
    user_preference = relationship("UserPreference", back_populates="user", uselist=False)
    
    favourite_users = relationship(
        "ProfileFavourite",
        foreign_keys="ProfileFavourite.user_id",
        back_populates="current_user"
    )
    
    favourited_by_users = relationship(
        "ProfileFavourite",
        foreign_keys="ProfileFavourite.favourite_user_id",
        back_populates="favourite_user"
    )
    
        