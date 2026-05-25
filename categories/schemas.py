# Category
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = ""
    icon_url: Optional[str] = ""

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    created_at: datetime

class Config:
    from_attributes = True


