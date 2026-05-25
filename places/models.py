 # import before Place
from datetime import datetime, timedelta, timezone
import enum
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint,Enum
from database import Base
from sqlalchemy.orm import relationship


MYANMAR_TZ = timezone(timedelta(hours=6, minutes=30))
# =======================
# Place Table
# =======================

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Place(Base):
    __tablename__="places"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    images = Column(JSON,default=[])  # store list of image URLs/paths
    rating = Column(Float, default=0.0)
    description = Column(String,default="")

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    subcategory_id = Column(Integer,ForeignKey("subcategories.id"),nullable=True)

    # location & Contact
    address = Column(String,default="")
    city = Column(String, default="Taunggyi")
    region = Column(String, default="Shan")
    country = Column(String, default="Myanmar")
    latitude = Column(Float,default=0.0)
    longitude = Column(Float,default=0.0)
    phone = Column(JSON,default=[])  # list of phone numbers
    website = Column(String,default="")
    email = Column(String, default="")
    
    # Opening Hours & Payments
    opening_hours = Column(JSON,default=[])  # list of strings
    payment_methods = Column(JSON, default=[])  # list of selected payment methods

    # Flags for app display & ads
    is_famous = Column(Boolean, default=False)
    is_popular = Column(Boolean, default=False)
    is_featured=Column(Boolean,default=False)
    is_active=Column(Boolean,default=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(MYANMAR_TZ)
        )
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(MYANMAR_TZ),
        onupdate=lambda:datetime.now(MYANMAR_TZ))
    

    # relationships
    category=relationship("Category",backref="places")
    subcategory=relationship("SubCategory",backref="places")
    owner = relationship("auth.models.User", backref="places")

    favorites = relationship("Favorite", back_populates="place", cascade="all, delete-orphan")
    visited = relationship("Visited", back_populates="place", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="place", cascade="all, delete-orphan")

# =======================
# Favorite Table
# =======================
class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    place_id = Column(Integer, ForeignKey("places.id"))

    place = relationship("Place", back_populates="favorites")

    # Ensure user can favorite a place only once
    __table_args__ = (UniqueConstraint('user_id', 'place_id', name='unique_user_place'),)


# =======================
# Visited Places Table
# =======================
class Visited(Base):
    __tablename__ = "visited"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    place_id = Column(Integer, ForeignKey("places.id"))
    visited_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(MYANMAR_TZ)
        )
    place = relationship("Place", back_populates="visited")

    # Ensure user can mark a place as visited only once
    __table_args__ = (UniqueConstraint('user_id', 'place_id', name='unique_visited'),)
