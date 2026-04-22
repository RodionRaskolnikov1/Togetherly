from enum import Enum
from sqlalchemy import Enum as SqlEnum


class VisibilityEnum(str, Enum):
    public = "public"
    private = "private"
    hidden = "hidden"

class GenderEnum(str, Enum):
    male = "male"
    female = "female"

class RoleEnum(str, Enum):
    user = "user"
    coordinator = "coordinator"
    super_admin = "super_admin"
    community_admin = "community_admin"
    member = "member"

class AccountStatusEnum(str, Enum):
    pending = "pending"
    email_verified = "email_verified"
    phone_verified = "phone_verified"
    active = "active"
    disabled = "disabled"
    
class ProfileStageEnum(str, Enum):
    pending = "pending"
    submitted = "submitted"
    verified = "verified"
    rejected = "rejected"

class DietEnum(str, Enum):
    veg = "veg"
    non_veg = "non_veg"     
    eggetarian = "eggetarian"

class YesNoOccasionalEnum(str, Enum):
    no = "no"
    yes = "yes"
    occasionally = "occasionally"

class PhysicalStatusEnum(str, Enum):
    normal = "normal"
    physically_challenged = "physically_challenged"
    
    
class MaritalStatusEnum(str, Enum):
    never_married = "never_married"
    divorced = "divorced"
    widowed = "widowed"
    
class ChildrenLivingWithEnum(str, Enum):
    self = "self"
    partner = "partner"
    both = "both"
    separately = "separately"

class ParentStatusEnum(str, Enum):
    alive = "alive"
    deceased = "deceased"
    not_disclosed = "not_disclosed"


class FamilyTypeEnum(str, Enum):
    nuclear = "nuclear"
    joint = "joint"
    extended = "extended"


class FamilyStatusEnum(str, Enum):
    middle_class = "middle_class"
    upper_middle_class = "upper_middle_class"
    rich = "rich"
    affluent = "affluent"
    
    
class CommunityRequestStatusEnum(str, Enum):
    approved = "approved"
    rejected = "rejected"
    pending = "pending"

class FamilyValuesEnum(str, Enum):
    traditional = "traditional"
    moderate = "moderate"
    liberal = "liberal"

class ManglikStatusEnum(str, Enum):
    yes = "yes"
    no = "no"
    partial = "partial"
    

class DocumentStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    
    
class EducationLevelEnum(str, Enum):
    below_ssc = "below_ssc" 
    ssc = "ssc" 
    hsc = "hsc"
    diploma = "diploma"
    graduate = "graduate" 
    masters = "masters" 
    higher_studies = "higher_studies"
    other = "other"
    
class PassingStatusEnum(str, Enum):
    completed = "completed"
    pursuing = "pursuing"
    failed = "failed"
    
class EmploymentStatusEnum(str, Enum):
    employed = "employed"
    business_owner = "business_owner"
    freelancer = "freelancer"
    unemployed = "unemployed"
    student = "student"
    retired = "retired"
    government_job = "government_job"
    
class EventStatusEnum(str, Enum):
    draft = "draft"
    published = "published"
    completed = "completed"
    cancelled = "cancelled"
    
    
class BloodGroupEnum(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
    
class BodyTypeEnum(str, Enum):
    slim = "slim"
    average = "average"
    athletic = "athletic"
    heavy = "heavy"
    
class ConnectionRequestEnum(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    
    
class AnnouncementPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

class AnnouncementStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class TicketStatusEnum(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    
class RegistrationStatusEnum(str, Enum):
    registered = "registered"
    cancelled = "cancelled"