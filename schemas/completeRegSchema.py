from schemas.profileSchema import ProfileCreate
from schemas.educationSchema import EducationCreate
from schemas.professionSchema import ProfessionCreate
from schemas.lifestyleschema import LifestyleCreate
from schemas.familyDetailsSchema import FamilyDetailsCreate
from schemas.horoscopeSchema import HoroscopeCreate
from pydantic import BaseModel

class completeRegSchema(BaseModel):
    profile: ProfileCreate
    education: EducationCreate
    profession: ProfessionCreate
    lifestyle: LifestyleCreate
    family_details: FamilyDetailsCreate
    horoscope: HoroscopeCreate