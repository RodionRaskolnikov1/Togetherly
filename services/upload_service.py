from fastapi import HTTPException, UploadFile

from sqlalchemy.orm import Session

from models import Profile, ProfileImage, UserImage

from utils.file_utils import upload_profile_image, upload_verification_document
from utils.file_utils import upload_profile_image
from utils.enums import DocumentStatusEnum

import cloudinary.uploader 

    
MAX_PROFILE_IMAGES = 5    

def upload_profile_image_service(
    file: UploadFile,
    db: Session,
    current_user,
    is_primary: bool = False
):
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=400, detail="Complete basic profile first")

    
    image_count = db.query(ProfileImage).filter(
        ProfileImage.profile_id == profile.id
    ).count()

    if image_count >= MAX_PROFILE_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_PROFILE_IMAGES} profile images allowed"
        )

    image_url, public_id = upload_profile_image(file, current_user.id)

    try:
        profile_image = ProfileImage(
            profile_id=profile.id,
            image_url=image_url,
            public_id=public_id,
            is_primary=is_primary
        )
        db.add(profile_image)
        db.flush()  

        if is_primary:
            db.query(ProfileImage).filter(
                ProfileImage.profile_id == profile.id,
                ProfileImage.id != profile_image.id
            ).update({"is_primary": False})

        db.commit()
        db.refresh(profile_image)

        return {
            "message": "Profile image uploaded successfully",
            "profile_image": profile_image
        }
        

    except Exception as e:
        db.rollback()
        if public_id:
            try:
                cloudinary.uploader.destroy(public_id)
            except Exception:
                pass  # Log this properly in production
        raise HTTPException(status_code=500, detail="Failed to save image")


def get_profile_images_service(
    db: Session,
    current_user
):
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(400, "Complete basic profile first")

    images = db.query(ProfileImage).filter(
        ProfileImage.profile_id == profile.id
    ).all()

    return images


def update_profile_photo_service(
    file: UploadFile,
    db: Session,
    current_user
):
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(400, "Complete basic profile first")

    # ✅ Find and delete the old primary image from ProfileImage table + Cloudinary
    old_primary = db.query(ProfileImage).filter(
        ProfileImage.profile_id == profile.id,
        ProfileImage.is_primary == True
    ).first()

    if old_primary:
        try:
            cloudinary.uploader.destroy(old_primary.public_id)
        except Exception:
            pass  # Log in production
        db.delete(old_primary)
        db.flush()

    # ✅ Upload new image to Cloudinary
    image_url, public_id = upload_profile_image(file, current_user.id)

    # ✅ Create new ProfileImage row marked as primary
    new_primary = ProfileImage(
        profile_id=profile.id,
        image_url=image_url,
        public_id=public_id,
        is_primary=True
    )
    db.add(new_primary)
    db.flush()

    # ✅ Sync Profile.profile_photo with the new image
    profile.profile_photo = image_url

    db.commit()
    db.refresh(profile)

    return {
        "message": "Profile photo updated successfully",
        "profile_photo": profile.profile_photo
    }


def delete_profile_image_service(
    image_id: str,
    db: Session,
    current_user
):
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=400, detail="Complete basic profile first")

    image = db.query(ProfileImage).filter(
        ProfileImage.id == image_id,
        ProfileImage.profile_id == profile.id
    ).first()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if image.public_id:
        try:
            cloudinary.uploader.destroy(image.public_id)
        except Exception as e:
            print(f"Cloudinary deletion failed for {image.public_id}: {e}")

    was_primary = image.is_primary
    db.delete(image)
    db.flush()

    if was_primary:
        next_image = db.query(ProfileImage).filter(
            ProfileImage.profile_id == profile.id
        ).first()
        if next_image:
            next_image.is_primary = True
            
    db.commit()

    return {"message": "Image deleted successfully"}


def upload_verification_document_service(
    file: UploadFile,
    db: Session,
    current_user,
    document_type : str, 
    community_id: str | None = None
):
    from models import VerificationDocuments
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(400, "Complete profile first")

    existing = db.query(VerificationDocuments).filter(
        VerificationDocuments.profile_id == profile.id,
        VerificationDocuments.community_id == community_id,
    ).first()

    file_url, public_id = upload_verification_document(
       file, profile.id
    )

    if existing:
        if existing.public_id:
            try:
                cloudinary.uploader.destroy(existing.public_id)
            except Exception:
                pass 
        existing.file_url = file_url
        existing.public_id = public_id
        existing.status = DocumentStatusEnum.pending
        existing.rejection_reason = None
        existing.reviewed_at = None
        existing.reviewed_by = None
    else:
        doc = VerificationDocuments(
            profile_id=profile.id,
            community_id=community_id,
            document_type=document_type, 
            file_url=file_url,
            public_id=public_id,
            status=DocumentStatusEnum.pending
        )
        db.add(doc)

    db.commit()

    return {
        "message": "Document uploaded successfully",
        "status": "pending_verification"
    }
