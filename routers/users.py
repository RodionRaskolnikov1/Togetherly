from typing import Optional
from fastapi import APIRouter, Depends, File, Request, UploadFile, Form
from sqlalchemy.orm import Session
from database import get_db

from models.user import User
from schemas.userSchema import UserRegister, OTPVerify, UserResponse, UpdateUserDetails
from schemas.profileSchema import ProfileResponse
from schemas.completeRegSchema import completeRegSchema
from schemas.communityRequestSchema import CommunityRequestCreate
from schemas.profileSchema import ProfileCreate
from schemas.educationSchema import EducationCreate
from schemas.professionSchema import ProfessionCreate, professionResponse
from schemas.lifestyleschema import LifestyleCreate
from schemas.familyDetailsSchema import FamilyDetailsCreate
from schemas.horoscopeSchema import HoroscopeCreate
from schemas.addressSchema import AddressResponse, AddressCreateRequest

from services.upload_service import (
    upload_profile_image_service, 
    upload_verification_document_service,
    get_profile_images_service,
    update_profile_photo_service,
    delete_profile_image_service
)
from utils.auth_utils import get_current_user

from services.registration_service import (
    start_registration_service,
    verify_registration_service,
    
    create_education_service,
    upsert_basic_profile_service,
    upsert_profession_service,
    upsert_lifestyle_service,
    upsert_family_details_service,
    upsert_horoscope_service,
    upsert_address_service,
    
    update_education_service,
    update_basic_details_service,
    
    get_static_data_service,
)
from services.otp_services import (
    resend_otp_service,
    send_verification_email_service,
    send_verification_phone_service,
    verify_secondary_email_service,
    verify_secondary_phone_service
)

from services.community_services import (
    create_community_request
)


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/start-registration")
def start_registration(payload: UserRegister, db: Session = Depends(get_db), request: Request = None):
    return start_registration_service(payload, db, request)

@router.post("/verify-registration", response_model=UserResponse)
def verify_registration(data: OTPVerify, db: Session = Depends(get_db), request: Request = None):
    return verify_registration_service(data, db, request)


@router.post("/profile/basic", response_model=ProfileResponse)
def upsert_basic_profile(
        payload: ProfileCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
        request: Request = None
    ):
    return upsert_basic_profile_service(payload, db, current_user, request)

@router.get("/profile/staticData")
def get_static_data(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_static_data_service(db, current_user)


@router.post("/profile/address", response_model=AddressResponse)
def upsert_address(
        payload: AddressCreateRequest,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
        request: Request = None
    ):
    return upsert_address_service(payload, db, current_user, request)

@router.post("/profile/educations", response_model=EducationCreate)
def create_education(
        payload: EducationCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
        request: Request = None
    ):
    return create_education_service(payload, db, current_user, request)

@router.put("/profile/educations/{education_id}", response_model=EducationCreate)
def update_education(
        education_id: str,
        payload: EducationCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
        request: Request = None
    ):
    return update_education_service(education_id, payload, db, current_user, request)


@router.post("/profile/profession", response_model=professionResponse)
def upsert_profession(
        payload: ProfessionCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
        request: Request = None
    ):
    return upsert_profession_service(payload, db, current_user, request)

@router.post("/profile/lifestyle", response_model=LifestyleCreate)
def upsert_lifestyle(
        payload: LifestyleCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
        request: Request = None
    ):
    return upsert_lifestyle_service(payload, db, current_user, request)


@router.post("/profile/familydetails", response_model=FamilyDetailsCreate)
def upsert_familydetails(
        payload: FamilyDetailsCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
        request: Request = None
    ):
    return upsert_family_details_service(payload, db, current_user, request)



@router.post("/profile/horoscope", response_model=HoroscopeCreate)
def upsert_horoscope(
        payload: HoroscopeCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
        request: Request = None
    ):
    return upsert_horoscope_service(payload, db, current_user, request)

# profile and documents uploading




@router.post("/profile/image")
def upload_profile_image_endpoint(
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return upload_profile_image_service(file, db, current_user, is_primary)


@router.get("/profile/images")
def get_profile_images(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_profile_images_service(db, current_user)


@router.put("/profile/photo")
def update_profile_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_profile_photo_service(file, db, current_user)


@router.delete("/profile/images/{image_id}")
def delete_profile_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return delete_profile_image_service(image_id, db, current_user)





@router.post("/documents/upload")
def upload_verification_document_endpoint(  
    document_type: str,
    file: UploadFile = File(...),
    community_id: str | None = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return upload_verification_document_service(
        file=file,
        document_type=document_type,
        community_id=community_id,
        db=db,
        current_user=current_user
    )

@router.post("/community/request")
def submit_community_request(
        payload: CommunityRequestCreate,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    return create_community_request (payload, db, current_user)

@router.post("/resend-otp")
def resend_otp(target: str, db: Session = Depends(get_db)): 
    return resend_otp_service(target, db)


@router.post("/send-email-verification")
def send_email_verification(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return send_verification_email_service(current_user, db)


@router.post("/send-phone-verification")
def send_phone_verification(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return send_verification_phone_service(current_user, db)


@router.post("/verify-email")
def verify_email(otp: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return verify_secondary_email_service(current_user, otp, db)


@router.post("/verify-phone")
def verify_phone(otp: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return verify_secondary_phone_service(current_user, otp, db)




@router.put("/update-basic-details")
def update_basic_details(
        payload: UpdateUserDetails,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
        request: Request = None
    ):
    return update_basic_details_service(payload, db, current_user, request)


@router.get("/profile/documents")
def get_my_documents(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
    from models.profile import Profile
    from models.verification_document import VerificationDocuments
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        return {"documents": []}
    
    documents = db.query(VerificationDocuments).filter(
        VerificationDocuments.profile_id == profile.id
    ).all()
    
    return {"documents": documents}