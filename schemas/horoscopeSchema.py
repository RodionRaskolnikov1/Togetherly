from pydantic import BaseModel
from datetime import date, time
from utils.enums import ManglikStatusEnum

class HoroscopeCreate(BaseModel):
    time_of_birth: time
    place_of_birth: str
    rashi: str
    nakshatra: str
    manglik_status: ManglikStatusEnum | None = None
    dosha_summary: str | None = None
    
