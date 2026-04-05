from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class VerificationDocumentBase(BaseModel):
    document_type: str

class VerificationDocumentCreate(VerificationDocumentBase):
    pass

class VerificationDocumentResponse(BaseModel):
    id: str
    profile_id: str
    community_id: Optional[str]

    document_type: str
    file_url: str
    status: str

    rejection_reason: Optional[str]

    uploaded_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)
        
        
class VerificationDocumentReview(BaseModel):
    status: str  # approved | rejected
    rejection_reason: Optional[str] = None
    coordinator_message: Optional[str] = None

