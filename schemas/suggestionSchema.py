from uuid import UUID
from pydantic import BaseModel

class CommunitySuggestionUser(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    gender: str
    city: str | None = None

    class Config:
        orm_mode = True
