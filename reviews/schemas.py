# -----------------------
# Review Schemas
# -----------------------
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class ReviewCreate(BaseModel):
    rating: float
    comment: Optional[str] = ""

class ReviewOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_avatar: str
    rating: float
    comment: str
    likes: int
    dislikes: int
    created_at: datetime
    class Config:
        model_config = {"from_attributes": True}

class ReviewReactionCreate(BaseModel):
    review_id: int
    reaction_type: str # "like" or "dislike"

