import os
import uuid
import shutil
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from utils.cloudinary_config import cloudinary

UPLOAD_DIR = "uploads/profile_images"

ALLOWED_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png"
]
MAX_SIZE_MB = 5


def upload_profile_image(file: UploadFile, user_id: str) -> tuple[str, str]:
    """Upload profile image and return (image_url, public_id)"""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only JPG and PNG images are allowed")
    
    unique_id = str(uuid.uuid4())
    result = cloudinary.uploader.upload(
        file.file,
        folder=f"matrimony/profile_images/{user_id}",
        public_id=unique_id,
        overwrite=False,
        resource_type="image"
    )
    return result["secure_url"], result["public_id"]

def upload_event_poster(file: UploadFile, event_id: str) -> tuple[str, str]:
    """Upload event poster image and return (image_url, public_id)"""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only JPG and PNG images are allowed")
    
    result = cloudinary.uploader.upload(
        file.file,
        folder=f"matrimony/events/{event_id}",
        public_id="poster",
        overwrite=True,
        resource_type="image"
    )
    return result["secure_url"], result["public_id"]

def upload_verification_document(
    file: UploadFile,
    profile_id: str
) -> tuple[str, str]:

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only PDF, JPG, PNG documents are allowed")

    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    extension = os.path.splitext(file.filename)[1].lower().lstrip(".")
    
    if size > MAX_FILE_SIZE:
        
        raise HTTPException(400, "File too large")
    
    result = cloudinary.uploader.upload(
        file.file,
        folder=f"matrimony/verification/{profile_id}",
        resource_type="auto",
        public_id=f"{profile_id}",
        format=extension,
        overwrite=True,
    )

    return result["secure_url"], result["public_id"]