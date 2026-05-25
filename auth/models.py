from datetime import datetime, timedelta, timezone
import enum
import json
from sqlalchemy import JSON,Column, DateTime,  Integer, String, Enum
from database import Base


MYANMAR_TZ = timezone(timedelta(hours=6, minutes=30))

# =======================
# User Table
# =======================

class UserRole(str, enum.Enum):
    ADMIN="admin"
    OWNER="owner"
    USER="user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    
    role=Column(Enum(UserRole),default=UserRole.USER,nullable=False)
    # Profile fields 
    bio = Column(String, default="[]")
    tagline = Column(String, default="")
    hometown = Column(String, default="")
    profile_image = Column(String, default="")  # file path or URL to avatar image

    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(MYANMAR_TZ)
        )
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(MYANMAR_TZ),
        onupdate=lambda:datetime.now(MYANMAR_TZ))


    # JSON
    def get_bio_list(self):
        try:
            return json.loads(self.bio)
        except:
            return []
        
    def set_bio_list(self,bio_list):
        self.bio=json.dumps(bio_list)

    