from pydantic import BaseModel

class CommunityRequestCreate(BaseModel):
    community_id: str
