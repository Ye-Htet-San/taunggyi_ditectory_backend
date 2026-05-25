from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator

class PlaceBase(BaseModel):
    title: str
    images: List[str]=[]
    rating: Optional[float] = 0.0
    description: Optional[str] = ""
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    address: Optional[str] = ""
    city: Optional[str] = "Taunggyi"
    region: Optional[str] = "Shan"
    country: Optional[str] = "Myanmar"
    phone: Optional[List[str]] = []
    email: Optional[str] = ""
    website: Optional[str] = ""
    opening_hours: Optional[List[dict]] = []
    latitude: Optional[float] = 0.0
    longitude: Optional[float] = 0.0
    is_famous: Optional[bool] = False
    is_popular: Optional[bool] = False
    is_featured:Optional[bool]=False
    is_active:Optional[bool]=True

class PlaceCreate(PlaceBase):
    pass

class PlaceOut(PlaceBase):
    id: int
    categoryName:Optional[str] =None
    subcategoryName:Optional[str]=None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    review_count: int = 0

   
    class Config:
         model_config = {"from_attributes": True,
                         "json_encoders": {datetime: lambda v: v.isoformat() if v else None},
                         } # orm_mode = True  # pydantic v1
         fields={
             "categoryName":"category_name",
             "subcategoryName": "subcategory_name"
         }
    # # ✅ Automatically convert datetime → string
    # @field_validator("created_at", "updated_at", mode="before")
    # @classmethod
    # def datetime_to_str(cls, v):
    #     if isinstance(v, datetime):
    #         return v.isoformat()
    #     return v

# -----------------------
# Favorite/Visited Schemas
# -----------------------

class FavoriteCreate(BaseModel):
    place_id: int # no user_id in body (we’ll use current_user)

class VisitedCreate(BaseModel):
    place_id: int


