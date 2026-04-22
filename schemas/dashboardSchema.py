from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import time, date, datetime

from utils.enums import (
    MaritalStatusEnum, EducationLevelEnum, 
    PassingStatusEnum, EmploymentStatusEnum, ManglikStatusEnum,
    FamilyTypeEnum, FamilyStatusEnum, FamilyValuesEnum, ParentStatusEnum,
    BloodGroupEnum, BodyTypeEnum, ChildrenLivingWithEnum
)


class EducationOut(BaseModel):
    id : str
    level : EducationLevelEnum
    status : PassingStatusEnum
    
    course_name : Optional[str] = None
    stream: Optional[str] = None
    institution_name: Optional[str] = None
    board_name: Optional[str] = None
    school_name: Optional[str] = None
    university_name: Optional[str] = None

    percentage_or_cgpa: Optional[float] = None
    passing_year: Optional[int] = None
    last_class_completed: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class LifestyleOut(BaseModel):
    diet: Optional[str] = None
    smoking: Optional[str] = None
    drinking: Optional[str] = None
    physical_status: Optional[str] = None
    health_issues: Optional[str] = None
    blood_group: Optional[BloodGroupEnum] = None
    body_type: Optional[BodyTypeEnum] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class FamilyOut(BaseModel):
    family_type: Optional[FamilyTypeEnum] = None
    family_status: Optional[FamilyStatusEnum] = None
    family_values: Optional[FamilyValuesEnum] = None
    
    father_status: Optional[ParentStatusEnum] = None
    father_occupation: Optional[str] = None

    mother_status: Optional[ParentStatusEnum] = None
    mother_name: str
    mother_occupation: Optional[str] = None

    number_of_family_members: Optional[int] = 0
    number_of_brothers: Optional[int] = 0
    number_of_sisters: Optional[int] = 0

    is_orphan: bool = False
    guardian_details: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
    
class currentAddressOut(BaseModel):
    
    street: str
    area: Optional[str] = None
    city_id : str
    state_id : str
    pin_code : str
    country_id : str
    
    model_config = ConfigDict(from_attributes=True)
    
class permanentAddressOut(BaseModel):
    
    street: str
    area: Optional[str] = None
    city_id : str
    state_id : str
    pin_code : str
    country_id : str
    
    model_config = ConfigDict(from_attributes=True)
    
class workAddressOut(BaseModel):
    
    city_id : str
    state_id : str
    pin_code : str
    country_id : str
    
    model_config = ConfigDict(from_attributes=True)
    
class horoscopeOut(BaseModel):
    time_of_birth: time
    place_of_birth: str
    rashi: str
    nakshatra: str
    manglik_status: ManglikStatusEnum | None = None
    dosha_summary: str | None = None
    
    model_config = ConfigDict(from_attributes=True)


class ProfessionOut(BaseModel):
    
    employment_status: EmploymentStatusEnum
    job_title: Optional[str] = None
    organization_name: Optional[str] = None
    annual_income: Optional[int] = None
    start_year: Optional[int] = None
    description: Optional[str] = None
    work_address : Optional[workAddressOut]
    
    model_config = ConfigDict(from_attributes=True)

class ProfileImageOut(BaseModel):
    image_url : str
    is_primary : bool
    
    model_config = ConfigDict(from_attributes=True)
    
class VerficationDocumentOut(BaseModel):
    file_url : str
    community_id : str
    uploaded_at : datetime
    document_type : str

    model_config = ConfigDict(from_attributes=True)
    
class ProfileDashboardOut(BaseModel):
    bio: Optional[str]
    marital_status: MaritalStatusEnum
    number_of_children: Optional[int]
    children_living_with : Optional[ChildrenLivingWithEnum]
    caste_id : str
    sub_caste_id : str
    religion_id : str

    current_address: Optional[currentAddressOut]
    permanent_address: Optional[permanentAddressOut]
    verification_documents: List[VerficationDocumentOut]
    
    horoscope: Optional[horoscopeOut]
    education_details: List[EducationOut]   
    profession_details: Optional[ProfessionOut]
    lifestyle: Optional[LifestyleOut]
    family_details: Optional[FamilyOut]
    profile_images: List[ProfileImageOut]

    model_config = ConfigDict(from_attributes=True)

class DashboardResponse(BaseModel):
    id: str
    first_name: str
    father_name : str
    last_name: str
    dob : date
    email: Optional[str]
    phone: Optional[str]
    gender: str
    account_status: str
    phone_verified: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    profile: Optional[ProfileDashboardOut]

    model_config = ConfigDict(from_attributes=True)
    

class CoordinatorUserDetailsResponse(BaseModel):
    id: str
    first_name: str
    father_name: str
    last_name: str
    dob: date
    email: Optional[str]
    phone: Optional[str]
    gender: str
    account_status: str
    phone_verified: bool
    
    profile: Optional[ProfileDashboardOut]

    model_config = ConfigDict(from_attributes=True)
    
    
class FeedUserOut(BaseModel):
    id: str
    first_name: str
    father_name: str
    last_name: str
    dob: date
    email: Optional[str]
    phone: Optional[str]
    gender: str
    account_status: str
    profile: Optional[ProfileDashboardOut]

    model_config = ConfigDict(from_attributes=True)
