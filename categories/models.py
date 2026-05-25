from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, DateTime, Integer, String
from database import Base


MYANMAR_TZ = timezone(timedelta(hours=6, minutes=30))

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, default="")
    icon_url = Column(String, default="")  # URL for category icon
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(MYANMAR_TZ))


