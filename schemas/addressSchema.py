from pydantic import BaseModel, ConfigDict
from typing import Optional

class AddressBase(BaseModel):
    street: str
    area: Optional[str] = None
    city_id : str
    state_id : str
    pin_code : str
    country_id : str
    
    model_config = ConfigDict(from_attributes=True)
    
class AddressCreateRequest(BaseModel):
    current_address: AddressBase
    permanent_address: AddressBase
    
class AddressResponse(BaseModel):
    current_address: AddressBase
    permanent_address: AddressBase
    
    
class WorkAddressCreate(BaseModel):
    city_id : str
    state_id : str
    pin_code : str
    country_id : str
    
    model_config = ConfigDict(from_attributes=True)
