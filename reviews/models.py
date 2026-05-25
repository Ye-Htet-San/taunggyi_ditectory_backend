
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from database import Base
from sqlalchemy.orm import relationship


MYANMAR_TZ = timezone(timedelta(hours=6, minutes=30))

# =======================
# Review Table
# =======================
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    place_id = Column(Integer, ForeignKey("places.id"))
    # user_name = Column(String)       # store user's display name
    # user_avatar = Column(String)     # store user's avatar URL/path
    rating = Column(Float)
    comment = Column(String)
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(MYANMAR_TZ)
        )
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(MYANMAR_TZ),
        onupdate=lambda:datetime.now(MYANMAR_TZ))

    user =relationship("User",backref="reviews")
    place = relationship("Place", back_populates="reviews")
    reactions = relationship("ReviewReaction", back_populates="review", cascade="all, delete-orphan")
# =======================
# Review Reaction Table
# =======================
class ReviewReaction(Base):
    __tablename__ = "review_reactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    review_id = Column(Integer, ForeignKey("reviews.id"))
    reaction_type = Column(String)  # "like" or "dislike"

    review = relationship("Review", back_populates="reactions")
    
    # Ensure one reaction per user per review
    __table_args__ = (UniqueConstraint('user_id', 'review_id', name='unique_user_review'),)


