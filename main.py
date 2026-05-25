import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import Base, engine
from auth.models import User
from auth.routes import router as auth_router
from places.routes import router as places_router
from categories.routes import router as categories_router
from subcategories.routes import router as subcategories_router
from reviews.routes import router as reviews_router
from fastapi.middleware.cors import CORSMiddleware

# Initialize the app
app = FastAPI()

# from config import settings
# print(f"SECRET_KEY loaded: {settings.SECRET_KEY}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], # Allow all http methods
    allow_headers=["*"], # Allow all header 
)

# Setup Upload Folders
os.makedirs("uploads/places", exist_ok=True)
os.makedirs("uploads/users", exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include Router
app.include_router(auth_router)
app.include_router(places_router)
app.include_router(categories_router)
app.include_router(subcategories_router)
app.include_router(reviews_router)

# Initialize Database
Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


# from auth.utils import hash_password
# print(hash_password("admin123"))
