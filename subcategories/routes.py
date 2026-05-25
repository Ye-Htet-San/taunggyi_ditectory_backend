from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth.dependencies import require_admin
from auth.models import User
from subcategories.models import SubCategory
from subcategories.schemas import SubCategoryCreate, SubCategoryOut
from database import get_db


router = APIRouter(prefix="/subcategories", tags=["SubCategories"])


# Get subcategories by category
@router.get("/{category_id}", response_model=list[SubCategoryOut])
def get_subcategories(category_id: int, db: Session = Depends(get_db)):
    return db.query(SubCategory).filter(SubCategory.category_id == category_id).all()

# Admin: Add subcategory

@router.post("/", response_model=SubCategoryOut)
def create_subcategory(
    subcat: SubCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # ✅ Check if subcategory already exists
    existing = db.query(SubCategory).filter(
        SubCategory.name == subcat.name,
        SubCategory.category_id == subcat.category_id
    ).first()

    if existing:
        return existing  # Return the existing subcategory instead of creating

    db_sub = SubCategory(**subcat.model_dump())
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub