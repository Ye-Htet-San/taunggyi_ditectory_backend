from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from auth.models import User
from auth.dependencies import get_current_user
from places.models import Place
from reviews.models import Review, ReviewReaction
from reviews.schemas import ReviewCreate, ReviewOut, ReviewReactionCreate
from fastapi.security import OAuth2PasswordBearer


router = APIRouter(prefix="/reviews", tags=["Reviews"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def update_place_rating(db: Session, place_id: int) -> None:
    avg = db.query(func.avg(Review.rating)).filter(Review.place_id == place_id).scalar()
    place = db.query(Place).filter(Place.id == place_id).first()
    if place:
        place.rating = float(avg or 0.0)
        db.add(place)


# -----------------------
# Get my review for a place
# -----------------------
@router.get("/my/{place_id}", response_model=ReviewOut)
def get_my_review(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(
        Review.place_id == place_id,
        Review.user_id == current_user.id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="No review yet")

    return {
        "id": review.id,
        "user_id": review.user_id,
        "user_name": current_user.username,
        "user_avatar": current_user.profile_image or "",
        "rating": review.rating,
        "comment": review.comment,
        "likes": review.likes,
        "dislikes": review.dislikes,
        "created_at": review.created_at,
    }

# -----------------------
# Add a review
# -----------------------
@router.post("/{place_id}", response_model=ReviewOut , status_code=status.HTTP_201_CREATED)
def add_review(place_id: int, 
               payload: ReviewCreate,
               db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):

    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    db_review = Review(
        user_id=current_user.id,
        place_id=place_id,
        rating=payload.rating,
        comment=payload.comment or ""
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    update_place_rating(db,place_id)
    db.commit()
    return {
        "id": db_review.id,
        "user_id": db_review.user_id,
        "user_name": current_user.username,
        "user_avatar": current_user.profile_image or "",
        "rating": db_review.rating,
        "comment": db_review.comment,
        "likes": db_review.likes,
        "dislikes": db_review.dislikes,
        "created_at": db_review.created_at,
    }

# -----------------------
# Get reviews for a place
# ----------------------- 
@router.get("/places/{place_id}", response_model=list[ReviewOut])
def get_reviews(place_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.place_id == place_id).all()
    out = []
    for r in reviews:
        user=db.query(User).filter(User.id == r.user_id).first()
        out.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_name": user.username if user else "",
            "user_avatar": user.profile_image if user else "",
            "rating": r.rating,
            "comment": r.comment,
            "likes": r.likes,
            "dislikes": r.dislikes,
            "created_at": r.created_at,
        })
    return out

# -----------------------
# Update reviews for a place
# -----------------------

@router.put("/{review_id}", response_model=ReviewOut)
def update_review(review_id: int, payload: ReviewCreate,
                  db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):

    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    review.rating = payload.rating
    review.comment = payload.comment or ""
    db.add(review)
    db.commit()
    db.refresh(review)
    return {
        "id": review.id,
        "user_id": review.user_id,
        "user_name": current_user.username,
        "user_avatar": current_user.profile_image or "",
        "rating": review.rating,
        "comment": review.comment,
        "likes": review.likes,
        "dislikes": review.dislikes,
        "created_at": review.created_at,
    }


# -----------------------
# Delete a review
# -----------------------
@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    place_id = review.place_id
    db.delete(review)
    db.commit()

    # Update place rating
    update_place_rating(db, place_id)
    db.commit()

    return {"message": "Review deleted successfully"}

# -----------------------
# Add or remove reaction
# -----------------------
@router.post("/{review_id}/reaction")
def add_or_remove_reaction(review_id: int, 
                           payload: ReviewReactionCreate,
                           db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):

    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Check if user already reacted
    existing = db.query(ReviewReaction).filter_by(
        user_id=current_user.id, review_id=review_id
        ).first()

    if existing:
        if existing.reaction_type == payload.reaction_type:
        # If user clicked again, remove reaction
            if existing.reaction_type == "like":
                review.likes =max(0, review.likes -1)
            else:
                review.dislikes = max(0,review.dislikes -1)
            db.delete(existing)
        else:
            # switch
            if existing.reaction_type == "like":
                review.likes = max(0, review.likes - 1); review.dislikes += 1
            else:
                review.dislikes = max(0, review.dislikes - 1); review.likes += 1
            existing.reaction_type = payload.reaction_type
    else:
        # new
        db.add(ReviewReaction(user_id=current_user.id, review_id=review_id,
                              reaction_type=payload.reaction_type))
        if payload.reaction_type == "like": review.likes += 1
        else: review.dislikes += 1

    db.add(review)
    db.commit()
    return {"message": "OK"}
