from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user, require_admin
from auth.schemas import ChangePassword,UserCreate, UserLogin, Token, UserUpdate
from auth.utils import ALGORITHM, SECRET_KEY, create_refresh_token, hash_password, verify_password, create_access_token
from auth.models import User, UserRole
from database import get_db
from auth.dependencies import oauth2_scheme
import os
router = APIRouter(prefix="/auth", tags=["Auth"])

UPLOADS_USERS_DIR = "uploads/users"
os.makedirs(UPLOADS_USERS_DIR, exist_ok=True)

# SIGNUP
@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == user.username) | (User.email == user.email)).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    new_user = User(
        
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role=UserRole.USER # assigned role as user
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

# LOGIN (username or email)
@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    login_id = user.identifier or user.email
    if not login_id:
        raise HTTPException(status_code=400, detail="Identifier or email is required")
    
    db_user = db.query(User).filter(
        (User.email == login_id) | (User.username == login_id)).first()
    
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": str(db_user.id)})
    refresh_token = create_refresh_token({"sub": str(db_user.id)})


    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Issue new access & refresh tokens
    new_access_token = create_access_token({"sub": user_id})
    new_refresh_token = create_refresh_token({"sub": user_id})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

# GET ACCOUNT INFO
@router.get("/me")
def get_account_info(current_user:User=Depends(get_current_user)):
    return{
        "userId":str(current_user.id),
        "userName":current_user.username,
        "userEmail":current_user.email,
        "userBio":current_user.get_bio_list(),
        "tagline":current_user.tagline,
        "homeTown":current_user.hometown,
        "avatarPath":current_user.profile_image
    }



# CHANGE PASSWORD
@router.post("/change-password")
def change_password(data:ChangePassword,
                    db:Session =Depends(get_db),
                    current_user:User =Depends(get_current_user)):
    if not verify_password(data.old_password,current_user.password):
        raise HTTPException(status_code=400,detail="Old password is incorrect")
    
    current_user.password=hash_password(data.new_password)
    db.commit()
    return {"message":"Password updated successfully"}



# EDIT PROFILE
@router.put("/profile/update")
def update_profile(
    data:UserUpdate,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
     # Update username if provided
    if data.userName is not None and data.userName != current_user.username:
        existing_user = db.query(User).filter(User.username == data.userName).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = data.userName

    print("Update payload:", data.dict())  # <-- see what Flutter sent
    print("Current user:", current_user.username)

    if data.userBio is not None:
        current_user.set_bio_list(data.userBio)

    if data.tagline is not None:
        current_user.tagline =data.tagline

    if data.homeTown is not None:
        current_user.hometown =data.homeTown

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return{
        "message":"Profile updated successfully",
        "user":{
            "userId":str(current_user.id),
            "userName":current_user.username,
            "userEmail":current_user.email,
            "userBio":current_user.get_bio_list(),
            "tagline":current_user.tagline,
            "homeTown":current_user.hometown,
            "avatarPath":current_user.profile_image
        }
    }

# PROFILE IMAGE UPLOAD
@router.post("/profile/upload-image")
def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = _ext_for_content_type(file.content_type)
    if not ext:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    filename = f"user_{current_user.id}_{uuid4().hex}{ext}"
    file_path = os.path.join(UPLOADS_USERS_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    relative_path = f"/{UPLOADS_USERS_DIR}/{filename}"
    current_user.profile_image = relative_path
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return {"avatarPath": relative_path}

def _ext_for_content_type(ct: str) -> str:
    # map for content types to extenstions]
    mapping={
        "image/jpeg": ".jpg",
        "image/pjpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/jpg": ".jpg",
        "application/octet-stream": ".jpg",  # fallback for Android
    }
    return mapping.get(ct.lower(),"")


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# ADMIN

# ---------------------------
# Get all users (Admin only)
# ---------------------------

@router.get("/admin/users")
def get_all_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role.value,
            "profile_image": u.profile_image,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "updated_at": u.updated_at.isoformat() if u.updated_at else None,
        }
        for u in users
    ]

# ---------------------------
# Helper: convert role string to UserRole (robust)
# ---------------------------
def _parse_role(role_str: str) -> UserRole:
    # Accept 'admin'/ 'Admin' / 'ADMIN' / 'Owner' / 'owner' / 'USER' etc.
    if not role_str:
        raise HTTPException(status_code=400, detail="Role is required")
    # Try by name (upper)
    name = role_str.strip().upper()
    if name in UserRole.__members__:
        return UserRole[name]
    # Try matching by enum value if values are different strings (case-insensitive)
    for e in UserRole:
        try:
            if str(e.value).lower() == role_str.strip().lower():
                return e
        except Exception:
            continue
    raise HTTPException(status_code=400, detail=f"Invalid role: {role_str}")


# ---------------------------
# Admin: promote user (to owner or admin)
# ---------------------------

@router.post("/admin/users/{user_id}/promote")
def promote_user(user_id: int, role: str =Query(...,description="Role to assign: owner or admin"), db: Session = Depends(get_db),
                 _: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
     # parse role
    new_role = _parse_role(role)
    user.role = new_role
    db.commit()
    return {"message": "Role updated", "user_id": user_id, "new_role": new_role.name}



# ---------------------------
# Admin: demote user (assign back to USER)
# ---------------------------
@router.post("/admin/users/{user_id}/demote")
def demote_user(user_id: int, role: str = Query("user", description="Role to assign (default user)"), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_role = _parse_role(role)
    user.role = new_role
    db.commit()
    return {"message": "Role updated", "user_id": user_id, "new_role": new_role.name}

# ---------------------------
# Admin: delete user
# ---------------------------
@router.delete("/admin/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted", "user_id": user_id}