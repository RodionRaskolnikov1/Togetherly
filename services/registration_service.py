from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import re

import crud.user as crud

from utils.enums import (
    GenderEnum, ProfileStageEnum, VisibilityEnum,
    PassingStatusEnum, RoleEnum, AccountStatusEnum
)

from utils.otp import (
    send_otp,
    verify_otp,
    save_pending_user,
    get_pending_user,
    delete_pending
)

from models import (
    User, Profile, EducationDetails,
    ProfessionDetails, Lifestyle, City, 
    State, FamilyDetails, Horoscope, UserSettings,
    PermanentAddress, CurrentAddress, WorkAddress
)

from utils.auth_utils import validate_location
from utils.hash import hash_password
from utils.logs import create_user_log

EMAIL_REGEX = r"[^@]+@[^@]+\.[^@]+"
PHONE_REGEX = r"^\+?[1-9]\d{7,14}$"

def detect_channel(target: str) -> bool:
    if re.fullmatch(EMAIL_REGEX, target):
        return True
    if re.fullmatch(PHONE_REGEX, target):
        return False
    raise HTTPException(400, "Invalid target format")

def start_registration_service(payload, db: Session, request):
    
    if payload.email and crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if payload.phone and crud.get_user_by_phone(db, payload.phone):
        raise HTTPException(status_code=400, detail="Phone already registered")

    pending = payload.model_dump()
    plain_pwd = pending.pop("password", None)
    
    if not plain_pwd:
        raise HTTPException(status_code=400, detail="Password required")
    pending["password_hash"] = hash_password(plain_pwd)
    

    dob_val = pending.get("dob")
    if isinstance(dob_val, date):
        pending["dob"] = dob_val.isoformat()
    elif dob_val in ("", None):
        pending["dob"] = None

    if pending.get("phone") == "":
        pending["phone"] = None

    key = payload.email or payload.phone
    if not key:
        raise HTTPException(status_code=400, detail="Either email or phone is required")
    
    save_pending_user(key, pending)
    via_email = detect_channel(key)
    send_otp(key, via_email=via_email)
    return {"message": "OTP sent"}


def verify_registration_service(data, db: Session, request):
    target = data.email or data.phone
    if not target:
        raise HTTPException(status_code=400, detail="Either email or phone required")

    if not verify_otp(target, data.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    pending = get_pending_user(target)
    if not pending:
        raise HTTPException(status_code=400, detail="Registration expired or not found")

    raw_dob = pending.get("dob")
    dob_obj = None
    if raw_dob:
        try:
            dob_obj = raw_dob if isinstance(raw_dob, date) else date.fromisoformat(raw_dob) 
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid date of birth format")
        
    pending["dob"] = dob_obj
    _validate_age(
        dob=dob_obj,
        gender=pending.get("gender", "")
    )

    new_user = User(
        email=pending.get("email"),
        phone=pending.get("phone"),
        password_hash=pending["password_hash"],
        first_name=pending.get("first_name"),
        father_name=pending.get("father_name"),
        last_name=pending.get("last_name"),
        dob=pending.get("dob"),
        gender=pending.get("gender"),
    )

    if data.email:
        target = data.email
        verified_channel = "email"
    elif data.phone:
        target = data.phone
        verified_channel = "phone"
    else:
        raise HTTPException(status_code=400, detail="Either email or phone required")
    
    new_user.email_verified = False
    new_user.phone_verified = False

    if verified_channel == "email":
        new_user.email_verified = True
    elif verified_channel == "phone":
        new_user.phone_verified = True

    if new_user.email_verified and new_user.phone_verified:
        new_user.account_status = AccountStatusEnum.active 
    elif new_user.email_verified:
        new_user.account_status = AccountStatusEnum.email_verified
    elif new_user.phone_verified:
        new_user.account_status = AccountStatusEnum.phone_verified

    try:
        db.add(new_user)
        db.flush()
        
        settings = UserSettings(
            user_id = new_user.id,
            visibility = VisibilityEnum.public
        )
        db.add(settings)
        
        db.commit()
        db.refresh(new_user)
        
        create_user_log(
            db=db,
            user_id=new_user.id,
            action="USER_REGISTERED",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
       
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user")

    delete_pending(target)
    return new_user


def upsert_basic_profile_service(payload, db: Session, current_user, request):
    
    # Only users can create profiles
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users can create profiles")
    
    try:
        profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
        
        if profile:
            profile.marital_status = payload.marital_status
            profile.caste_id = payload.caste_id
            profile.sub_caste_id = payload.sub_caste_id
            profile.religion_id = payload.religion_id
            profile.number_of_children = payload.number_of_children
            profile.children_living_with = payload.children_living_with
            profile.bio = payload.bio
            
        else:
            profile = Profile(
                user_id=current_user.id,
                marital_status=payload.marital_status,
                caste_id = payload.caste_id,
                sub_caste_id = payload.sub_caste_id,
                religion_id = payload.religion_id,
                number_of_children=payload.number_of_children,
                children_living_with=payload.children_living_with,
                bio = payload.bio,
                profile_stage= ProfileStageEnum.pending
            )     
            db.add(profile)
        
        db.commit()
        db.refresh(profile)
        
        create_user_log (
            db=db,
            user_id=current_user.id,
            action="Profile Basic Details Updated",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create profile")
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "user_name": f"{(current_user.first_name or '').strip()} {(current_user.last_name or '').strip()}".strip(),
    } 
    
def upsert_address_service(payload, db : Session, current_user, request):
    
    # Only users can access profile details
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users can access profile details")
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(400, "Complete basic profile first")
    
    current = payload.current_address
    permanent = payload.permanent_address
    
    try:
        validate_location(
            city_id=current.city_id,
            state_id=current.state_id,
            country_id=current.country_id,
            db=db
        )
        
        validate_location(
            city_id=permanent.city_id,
            state_id=permanent.state_id,
            country_id=permanent.country_id,
            db=db
        )
        
        current_address = db.query(CurrentAddress).filter(
            CurrentAddress.profile_id == profile.id
        ).first()

        if current_address:
            current_address.street = current.street
            current_address.area = current.area
            current_address.city_id = current.city_id  
            current_address.state_id = current.state_id
            current_address.pin_code = current.pin_code
            current_address.country_id = current.country_id
        else:
            current_address = CurrentAddress(
                profile_id=profile.id,
                street=current.street,
                area=current.area,
                city_id=current.city_id,
                state_id=current.state_id,
                pin_code=current.pin_code,
                country_id=current.country_id
            )
            db.add(current_address)
        
        permanent_address = db.query(PermanentAddress).filter(
            PermanentAddress.profile_id == profile.id
        ).first()

        if permanent_address:
            permanent_address.street = permanent.street
            permanent_address.area = permanent.area
            permanent_address.city_id = permanent.city_id
            permanent_address.state_id = permanent.state_id
            permanent_address.pin_code = permanent.pin_code
            permanent_address.country_id = permanent.country_id
        else:
            permanent_address = PermanentAddress(
                profile_id=profile.id,
                street=permanent.street,
                area=permanent.area,
                city_id=permanent.city_id,
                state_id=permanent.state_id,
                pin_code=permanent.pin_code,
                country_id=permanent.country_id
            )
            db.add(permanent_address)
            
        db.commit()
        db.refresh(current_address)
        db.refresh(permanent_address)
        
        create_user_log(
            db=db,
            user_id=current_user.id,
            action="PROFILE_ADDRESS_UPSERTED",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "current_address" : current_address,
            "permanent_address" : permanent_address  
        }
        
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to upsert address details"
        )
    
    
def create_education_service(payload, db: Session, current_user, request):
    
    # Only users can access profile details
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users can access profile details")
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(400, "Complete basic profile first")

    if payload.status == PassingStatusEnum.pursuing:
        existing = db.query(EducationDetails).filter(
            EducationDetails.profile_id == profile.id,
            EducationDetails.status == PassingStatusEnum.pursuing
        ).first()

        if existing:
            raise HTTPException(
                400,
                "You already have a pursuing education"
            )
    try:
        education = EducationDetails(
            profile_id=profile.id,
            level=payload.level,
            status=payload.status,
            course_name=payload.course_name,
            stream=payload.stream,
            institution_name=payload.institution_name,
            board_name=payload.board_name,
            school_name=payload.school_name,
            university_name=payload.university_name,
            percentage_or_cgpa=payload.percentage_or_cgpa,
            passing_year=payload.passing_year,
            last_class_completed=payload.last_class_completed,
        )

        db.add(education)
        db.commit()
        db.refresh(education)

        create_user_log(
            db=db,
            user_id=current_user.id,
            action="PROFILE_EDUCATION_CREATED",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return education    
    
    except SQLAlchemyError:
        db.rollback()   
        raise HTTPException(
            500, "Failed to upsert education details"
        ) 
        
def update_education_service(education_id : str, payload, db: Session, current_user, request):
     
    # Only users can access profile details
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users can access profile details")
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(400, "Complete basic profile first")
       
    
    education = db.query(EducationDetails).filter(
        EducationDetails.id == education_id,
        EducationDetails.profile_id == profile.id
    ).first()
    
    if not education:
        raise HTTPException(404, "Education record not found")
    
    if payload.status == PassingStatusEnum.pursuing:
        existing = db.query(EducationDetails).filter(
            EducationDetails.profile_id == profile.id,
            EducationDetails.status == PassingStatusEnum.pursuing,
            EducationDetails.id != education.id
        ).first()

        if existing:
            raise HTTPException(
                400,
                "You already have a pursuing education"
            ) 
    

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(education, field, value)

    db.commit()
    db.refresh(education)

    create_user_log(
        db=db,
        user_id=current_user.id,
        action="PROFILE_EDUCATION_UPDATED",
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return education
     

def upsert_profession_service(payload, db: Session, current_user, request):

    # Only users can access profile details
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users can access profile details")
    
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(400, "Complete basic profile first")

    try:
        profession = db.query(ProfessionDetails).filter(
            ProfessionDetails.profile_id == profile.id
        ).first()

        if profession:
            profession.employment_status = payload.employment_status
            profession.job_title = payload.job_title
            profession.organization_name = payload.organization_name
            profession.annual_income = payload.annual_income
            profession.start_year = payload.start_year
            profession.description = payload.description
        else:
            profession = ProfessionDetails(
                profile_id=profile.id,
                employment_status=payload.employment_status,
                job_title=payload.job_title,
                organization_name=payload.organization_name,
                annual_income=payload.annual_income,
                start_year=payload.start_year,
                description=payload.description
            )
            db.add(profession)
            db.flush()
            
        if payload.work_address:
                
            validate_location(
                city_id=payload.work_address.city_id,
                state_id=payload.work_address.state_id,
                country_id=payload.work_address.country_id,
                db=db
            )
                
            work_address = db.query(WorkAddress).filter(
                WorkAddress.profession_id == profession.id
            ).first()

            if work_address:
                work_address.city_id = payload.work_address.city_id
                work_address.state_id = payload.work_address.state_id
                work_address.pin_code = payload.work_address.pin_code
                work_address.country_id = payload.work_address.country_id
            else:
                work_address = WorkAddress(
                    profession_id=profession.id,
                    city_id=payload.work_address.city_id,
                    state_id=payload.work_address.state_id,
                    pin_code=payload.work_address.pin_code,
                    country_id=payload.work_address.country_id
                )
                db.add(work_address)
        
        db.commit()
        db.refresh(profession)
        
        create_user_log(
            db=db,
            user_id=current_user.id,
            action="PROFILE_PROFESSION_UPSERTED",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return {
            "id": profession.id,
            "employment_status": profession.employment_status,    
            "job_title" : profession.job_title,
            "organization_name" : profession.organization_name,
            "annual_income" : profession.annual_income,
            "start_year" : profession.start_year,
            "description" : profession.description
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Failed to upsert profession details")

def upsert_lifestyle_service(payload, db: Session, current_user, request):

    # Only users can access profile details
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users can access profile details")
    
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(400, "Complete basic profile first")

    try:
        lifestyle = db.query(Lifestyle).filter(
            Lifestyle.profile_id == profile.id
        ).first()

        if lifestyle:
            lifestyle.diet = payload.diet
            lifestyle.smoking = payload.smoking
            lifestyle.drinking = payload.drinking
            lifestyle.physical_status = payload.physical_status
            lifestyle.health_issues = payload.health_issues
            lifestyle.blood_group = payload.blood_group
            lifestyle.body_type = payload.body_type
            lifestyle.height = payload.height
            lifestyle.weight = payload.weight
        else:
            lifestyle = Lifestyle(
                profile_id=profile.id,
                diet=payload.diet,
                smoking=payload.smoking,
                drinking=payload.drinking,
                physical_status=payload.physical_status,
                health_issues=payload.health_issues,
                blood_group=payload.blood_group,
                body_type=payload.body_type,
                height=payload.height,
                weight=payload.weight
            )
            db.add(lifestyle)

        db.commit()
        db.refresh(lifestyle)

        create_user_log(
            db=db,
            user_id=current_user.id,
            action="PROFILE_LIFESTYLE_UPSERTED",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return {
            "profile_id": lifestyle.profile_id,
            "diet": lifestyle.diet,
            "smoking": lifestyle.smoking,
            "drinking": lifestyle.drinking,
            "physical_status": lifestyle.physical_status,
            "health_issues": lifestyle.health_issues,
            "blood_group": lifestyle.blood_group,
            "body_type": lifestyle.body_type,
            "height": lifestyle.height,
            "weight": lifestyle.weight
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Failed to upsert lifestyle details")


def upsert_family_details_service(payload, db: Session, current_user, request):

    # Only users can access profile details
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users can access profile details")
    
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(400, "Complete basic profile first")

    try:
        family = db.query(FamilyDetails).filter(
            FamilyDetails.profile_id == profile.id
        ).first()

        if family:
            family.family_type = payload.family_type
            family.family_status = payload.family_status
            family.family_values = payload.family_values
            family.father_status = payload.father_status
            family.father_occupation = payload.father_occupation
            family.mother_status = payload.mother_status
            family.mother_name = payload.mother_name
            family.mother_occupation = payload.mother_occupation
            family.number_of_family_members = payload.number_of_family_members
            family.number_of_brothers = payload.number_of_brothers
            family.number_of_sisters = payload.number_of_sisters
            family.is_orphan = payload.is_orphan
            family.guardian_details = payload.guardian_details
        else:
            family = FamilyDetails(
                profile_id=profile.id,
                family_type=payload.family_type,
                family_status=payload.family_status,
                family_values=payload.family_values,
                father_status=payload.father_status,
                father_occupation=payload.father_occupation,
                mother_status=payload.mother_status,
                mother_name=payload.mother_name,
                mother_occupation=payload.mother_occupation,
                number_of_family_members=payload.number_of_family_members,
                number_of_brothers=payload.number_of_brothers,
                number_of_sisters=payload.number_of_sisters,
                is_orphan=payload.is_orphan,
                guardian_details=payload.guardian_details
            )
            db.add(family)

        db.commit()
        db.refresh(family)

        create_user_log(
            db=db,
            user_id=current_user.id,
            action="PROFILE_FAMILY_UPSERTED",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return {
            "profile_id": family.profile_id,
            "family_type": family.family_type,
            "family_status": family.family_status,
            "family_values": family.family_values,
            "father_status": family.father_status,
            "father_occupation": family.father_occupation,
            "mother_status": family.mother_status,
            "mother_name": family.mother_name,
            "mother_occupation": family.mother_occupation,
            "number_of_family_members": family.number_of_family_members,
            "number_of_brothers": family.number_of_brothers,
            "number_of_sisters": family.number_of_sisters,
            "is_orphan": family.is_orphan,
            "guardian_details": family.guardian_details
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Failed to upsert family details")

    
def upsert_horoscope_service(payload, db: Session, current_user, request):

    # Only users can access profile details
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users can access profile details")
    
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(400, "Complete basic profile first")

    try:
        horoscope = db.query(Horoscope).filter(
            Horoscope.profile_id == profile.id
        ).first()

        if horoscope:
            horoscope.time_of_birth = payload.time_of_birth
            horoscope.place_of_birth = payload.place_of_birth
            horoscope.rashi = payload.rashi
            horoscope.nakshatra = payload.nakshatra
            horoscope.manglik_status = payload.manglik_status
            horoscope.dosha_summary = payload.dosha_summary
        else:
            horoscope = Horoscope(
                profile_id=profile.id,
                time_of_birth=payload.time_of_birth,
                place_of_birth=payload.place_of_birth,
                rashi=payload.rashi,
                nakshatra=payload.nakshatra,
                manglik_status=payload.manglik_status,
                dosha_summary=payload.dosha_summary
            )
            db.add(horoscope)

        db.commit()
        db.refresh(horoscope)

        create_user_log(
            db=db,
            user_id=current_user.id,
            action="PROFILE_HOROSCOPE_UPSERTED",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        return {
            "profile_id": horoscope.profile_id,
            "time_of_birth": horoscope.time_of_birth,
            "place_of_birth": horoscope.place_of_birth,
            "rashi": horoscope.rashi,
            "nakshatra": horoscope.nakshatra,
            "manglik_status": horoscope.manglik_status,
            "dosha_summary": horoscope.dosha_summary
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Failed to upsert horoscope details")


def _validate_age(dob: date, gender: str):
    if not dob:
        return
    
    today = date.today()
    age = today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day)
    )

    if gender == GenderEnum.male and age < 21:
        raise HTTPException(400, "Male must be 21+")
    if gender == GenderEnum.female and age <18:
        raise HTTPException(400, "Female must be 18+")
    
    
def get_static_data_service(db: Session, current_user: User):
    
    # Only users can access profile details
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users can access profile details")
    
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(400, "Complete basic profile first")

    
    father_name = db.query(User.father_name).filter(User.id == current_user.id).scalar()
    dob = db.query(User.dob).filter(User.id == current_user.id).scalar()
    
    return {
        "Father Name" : father_name,
        "Date of birth" : dob
    }
    

def update_basic_details_service(payload, db: Session, current_user : User, request):
    
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    
    if "dob" in update_data:
        raw_dob = update_data.get("dob")
        if raw_dob:
            try:
                dob_obj = raw_dob if isinstance(raw_dob, date) else date.fromisoformat(raw_dob)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Invalid date format")

            _validate_age(
                dob=dob_obj,
                gender=update_data.get("gender", user.gender)
            )
            user.dob = dob_obj
        else:
            user.dob = None

    update_data.pop("dob", None)
        
    update_data.pop("id", None)

    
    for field, value in update_data.items():
        setattr(user, field, value)
        
    try:
        db.commit()
        db.refresh(user)

        create_user_log(
            db=db,
            user_id=user.id,
            action="USER_UPDATED",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update user")

    return user