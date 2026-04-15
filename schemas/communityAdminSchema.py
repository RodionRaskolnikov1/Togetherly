from pydantic import BaseModel

class CommunityAdminCreate(BaseModel):
    user_id: str
    community_id: str


class CommunityAdminUserOut(BaseModel):
    id: str
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


