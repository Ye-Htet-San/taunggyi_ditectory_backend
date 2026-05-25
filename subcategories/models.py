from sqlalchemy import Column, ForeignKey, Integer, String

from database import Base
from sqlalchemy.orm import relationship

class SubCategory(Base):
    __tablename__="subcategories"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,nullable=False,unique=True)
    category_id=Column(Integer, ForeignKey("categories.id"))

    category = relationship("Category", backref="subcategories")