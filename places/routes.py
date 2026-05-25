import json
import os
import shutil
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from categories.models import Category
from database import get_db
from auth.dependencies import get_current_user, require_admin, require_owner
from auth.models import User
from places.models import ApprovalStatus, Place, Favorite, Visited
from places.schemas import FavoriteCreate, PlaceCreate, PlaceOut, VisitedCreate
from reviews.models import Review

router = APIRouter(prefix="/places", tags=["Places"])

UPLOAD_DIR = "uploads/places"

os.makedirs(UPLOAD_DIR, exist_ok=True)
# -----------------------
# Places CRUD
# -----------------------
# Owner creates a place (status=PENDING)
@router.post("/", response_model=PlaceOut)
def create_place(place: PlaceCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(require_owner)):
    db_place = Place(**place.model_dump(),owner_id=current_user.id,status=ApprovalStatus.PENDING)
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    return db_place

# 1️⃣ Get all approved places
@router.get("/", response_model=List[PlaceOut])
def get_places(db: Session = Depends(get_db)):
    places= db.query(Place).filter(Place.status ==ApprovalStatus.APPROVED).all()
    # return places
    return [
        PlaceOut(
            **p.__dict__,
            categoryName=p.category.name if p.category else None,
            subcategoryName=p.subcategory.name if p.subcategory else None,
            review_count=db.query(func.count()).select_from(Review).filter(Review.place_id == p.id).scalar()
         
        )
        for p in places
    ]

# 2️⃣ Get place by ID (only approved or owner/admin can see)
@router.get("/{place_id}", response_model=PlaceOut)
def get_place(place_id: int, db: Session = Depends(get_db),
              current_user:User =Depends(get_current_user)):
    place = db.query(Place).filter(Place.id == place_id).first()

    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    
    if place.status != ApprovalStatus.APPROVED and current_user.role not in ("admin","owner"):
        raise HTTPException(status_code=403,detail="Access denied")

    review_count=db.query(func.count()).select_from(Review).filter(Review.place_id == place_id).scalar()

    return PlaceOut(
        **place.__dict__,
        categoryName=place.category.name if place.category else None,
        subcategoryName=place.subcategory.name if place.subcategory else None,
        review_count=review_count
    )

# Count places per category (only approved)
@router.get("/analytics/places-per-category")
def places_per_category(db: Session = Depends(get_db)):
    results = (
        db.query(Place.category_id, Category.name, func.count(Place.id))
        .join(Category, Place.category_id == Category.id)
        .filter(Place.status == ApprovalStatus.APPROVED)
        .group_by(Place.category_id, Category.name)
        .all()
    )
    return [{"category": r[1], "count": r[2]} for r in results]

# Admin: List pending places
@router.get("/admin/pending",response_model=List[PlaceOut])
def admin_pending_places(db: Session =Depends(get_db),
                         _:User=Depends(require_admin)):
    return db.query(Place).filter(Place.status == ApprovalStatus.PENDING).all()

# Admin creates a place (auto-approved)

@router.post("/admin/create", response_model=PlaceOut)
async def admin_create_place(
    title: str = Form(...),
    category_id: int = Form(...),
    subcategory_id: int | None = Form(...),
    description: str = Form(""),
    address: str = Form(""),
    city: str = Form("Taunggyi"),
    region: str = Form("Shan"),
    country: str = Form("Myanmar"),
    latitude: float = Form(0.0),
    longitude: float = Form(0.0),
    phone_number: str = Form(""),
    website: str = Form(""),
    email: str = Form(""),
    opening_hours: str = Form("[]"),
    payment_methods: str = Form("[]"),
    is_famous: bool = Form(False),
    is_popular: bool = Form(False),
    is_featured: bool = Form(False),
    is_active: bool = Form(True),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    # ✅ Save uploaded images
    image_paths = []
    for img in images:
        file_path = os.path.join(UPLOAD_DIR, img.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(img.file, buffer)
        image_paths.append(f"uploads/places/{img.filename}")  # relative path

    # ✅ Save place details in DB
    db_place = Place(
        title=title,
        category_id=category_id,
        subcategory_id=subcategory_id,
        description=description,
        address=address,
        city=city,
        region=region,
        country=country,
        latitude=latitude,
        longitude=longitude,
        phone=[p.strip() for p in phone_number.split(",") if p.strip()],
        website=website,
        email=email,
        opening_hours=json.loads(opening_hours),
        payment_methods=json.loads(payment_methods),
        is_famous=is_famous,
        is_popular=is_popular,
        is_featured=is_featured,
        is_active=is_active,
        images=image_paths,  # ✅ store image paths
        owner_id=current_user.id,
        status=ApprovalStatus.APPROVED
    )

    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    return db_place

@router.put("/admin/update/{place_id}", response_model=PlaceOut)
async def admin_update_place(
    place_id: int,
    title: str = Form(...),
    category_id: int = Form(...),
    subcategory_id: int | None = Form(None),
    description: str = Form(""),
    address: str = Form(""),
    city: str = Form("Taunggyi"),
    region: str = Form("Shan"),
    country: str = Form("Myanmar"),
    latitude: float = Form(0.0),
    longitude: float = Form(0.0),
    phone_number: str = Form(""),
    website: str = Form(""),
    email: str = Form(""),
    opening_hours: str = Form("[]"),
    payment_methods: str = Form("[]"),
    is_famous: bool = Form(False),
    is_popular: bool = Form(False),
    is_featured: bool = Form(False),
    is_active: bool = Form(True),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    p = db.query(Place).filter(Place.id == place_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Place not found")

    # ✅ update fields
    p.title = title
    p.category_id = category_id
    p.subcategory_id = subcategory_id
    p.description = description
    p.address = address
    p.city = city
    p.region = region
    p.country = country
    p.latitude = latitude
    p.longitude = longitude
    p.phone = [ph.strip() for ph in phone_number.split(",") if ph.strip()]
    p.website = website
    p.email = email
    p.opening_hours = json.loads(opening_hours)
    p.payment_methods = json.loads(payment_methods)
    p.is_famous = is_famous
    p.is_popular = is_popular
    p.is_featured = is_featured
    p.is_active = is_active

    # ✅ replace images if new ones uploaded
    if images:
        image_paths = []
        for img in images:
            file_path = os.path.join(UPLOAD_DIR, img.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            image_paths.append(f"uploads/places/{img.filename}")
        p.images = image_paths

    db.commit()
    db.refresh(p)
    return p


# Admin delete a place 
@router.delete("/admin/{place_id}")
def admin_delete_place(place_id: int, db: Session = Depends(get_db),
                       _: User = Depends(require_admin)):
    p = db.query(Place).filter(Place.id == place_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Place not found")
    db.delete(p)
    db.commit()
    return {"message": "Place deleted"}

# Admin: Approve
@router.patch("/admin/{place_id}/approve",response_model=PlaceOut)
def admin_approve_place(place_id: int,db:Session=Depends(get_db),
                        _:User=Depends(require_admin)):
    p=db.query(Place).filter(Place.id == place_id).first()
    if not p:
        raise HTTPException(status_code=404,detail="Place not found")
    p.status=ApprovalStatus.APPROVED
    db.commit()
    db.refresh(p)
    return p

# Admin: Reject
@router.patch("/admin/{place_id}/reject",response_model=PlaceOut)
def admin_reject_place(place_id: int,db:Session=Depends(get_db),
                       _:User=Depends(require_admin)):
    p=db.query(Place).filter(Place.id == place_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Place not found")
    p.status = ApprovalStatus.REJECTED
    db.commit()
    db.refresh(p)
    return p


# -----------------------
# Favorites
# -----------------------
@router.post("/{place_id}/favorite")
def toggle_favorite(place_id: int, 
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    
    existing = db.query(Favorite).filter_by(user_id=current_user.id, place_id=place_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"message": "Removed from favorites"}
    
    db_fav = Favorite(user_id=current_user.id, place_id=place_id)
    db.add(db_fav)
    db.commit()
    return {"message": "Added to favorites"}

@router.get("/me/favorites", response_model=List[int])
def my_favorites(db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    favs = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    return [f.place_id for f in favs]

# -----------------------
# Visited
# -----------------------
@router.post("/{place_id}/visited")
def mark_visited(place_id: int, 
                 db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    place = db.query(Place).filter(Place.id== place_id).first()

    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    
    exists = db.query(Visited).filter_by(user_id=current_user.id, place_id=place_id).first()
    if exists:
        return {"message": "Already marked visited"}
    
    dbv = Visited(user_id=current_user.id, place_id=place_id)
    db.add(dbv)
    db.commit()
    return {"message": "Marked as visited"}

@router.get("/me/visited", response_model=List[int])
def my_visited(db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    rows = db.query(Visited).filter(Visited.user_id == current_user.id).all()
    return [v.place_id for v in rows]
