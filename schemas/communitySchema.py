from pydantic import BaseModel
from typing import Optional

class CommunityCreate(BaseModel):
    city_id: str
    religion_id: str
    caste_id: str
    sub_caste_id: str
    description : str
    display_name: str   
    
