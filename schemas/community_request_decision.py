# schemas/community_request_decision.py
from pydantic import BaseModel
from typing import Literal

class CommunityRequestDecision(BaseModel):
    action: Literal["approve", "reject"]
