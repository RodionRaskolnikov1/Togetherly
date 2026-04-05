from pydantic import BaseModel, EmailStr, field_validator, model_validator, Field
from datetime import date
from typing import Optional
from utils.enums import GenderEnum

class UserRegister(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str
    first_name: str
    father_name : str
    last_name: str
    dob: date
    gender: GenderEnum

    @field_validator("email", mode="before")
    def empty_email_to_none(cls, v):
        if v == "":
            return None
        return v
    
    @model_validator(mode="after")
    def require_email_or_phone(cls, values):
        if not values.email and not values.phone:
            raise ValueError("Either email or phone must be provided.")
        return values

class OTPRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @model_validator(mode="after")
    def require_contact(cls, values):
        if not values.email and not values.phone:
            raise ValueError("Either email or phone must be provided.")
        return values


class OTPVerify(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp: str
    
    @field_validator("email", mode="before")
    def empty_email_to_none(cls, v):
        if v == "":
            return None
        return v

    @field_validator("otp")
    def check_otp(cls, v: str) -> str:
        if len(v) != 6 or not v.isdigit():
            raise ValueError("OTP must be 6 digits.")
        return v

    @model_validator(mode="after")
    def require_contact(cls, values):
        if not values.email and not values.phone:
            raise ValueError("Email or phone required.")
        return values

class UserResponse(BaseModel):
    id: str
    email: Optional[str]
    phone: Optional[str]
    first_name: Optional[str]
    father_name: Optional[str]
    last_name: Optional[str]
    account_status: str
    gender: str

    model_config = {"from_attributes": True}


class Login(BaseModel):
    identifier: str 
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SetupPassword(BaseModel):
    token : str
    email: Optional[str]
    phone: Optional[str]
    first_name: Optional[str]
    father_name: Optional[str]
    last_name: Optional[str]
    dob: date
    gender: GenderEnum
    password : str = Field(min_length=8)


class PasswordResetRequest(BaseModel):
    identifier: str


class PasswordResetConfirm(BaseModel):
    token: str
    password: str = Field(min_length=8)
    
class PasswordResetUser(BaseModel):
    old_password : str
    new_password : str = Field(min_length=8)



class ForgotPasswordRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
 
    @field_validator("email", mode="before")
    def empty_email_to_none(cls, v):
        if v == "":
            return None
        return v
 
    @model_validator(mode="after")
    def require_contact(cls, values):
        if not values.email and not values.phone:
            raise ValueError("Either email or phone must be provided.")
        return values
 
 
class ForgotPasswordVerify(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp: str
    new_password: str = Field(min_length=8)
 
    @field_validator("email", mode="before")
    def empty_email_to_none(cls, v):
        if v == "":
            return None
        return v
 
    @field_validator("otp")
    def check_otp(cls, v: str) -> str:
        if len(v) != 6 or not v.isdigit():
            raise ValueError("OTP must be 6 digits.")
        return v
 
    @model_validator(mode="after")
    def require_contact(cls, values):
        if not values.email and not values.phone:
            raise ValueError("Either email or phone must be provided.")
        return values




class UpdateUserDetails(BaseModel):
    first_name: Optional[str]
    father_name: Optional[str]
    last_name: Optional[str]
    dob: Optional[date]
    gender: Optional[GenderEnum]
    
    
class MemberCreate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: str
    father_name : str
    last_name: str
    dob: date
    gender: GenderEnum