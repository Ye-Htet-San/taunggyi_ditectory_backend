import json
from database import SessionLocal
from places.models import Place

db = SessionLocal()

with open("seeds/places_seed.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for p in data:
    # Check if place already exists
    if not db.query(Place).filter_by(title=p["title"]).first():
        # Make sure images, phone, opening_hours are lists
        images = p.get("images") or []
        phone = p.get("phone") or []
        opening_hours = p.get("opening_hours") or []

        place = Place(
            title=p["title"],
            images=images,
            rating=p.get("rating", 0.0),
            description=p.get("description", ""),
            category=p.get("category", ""),
            subcategory=p.get("subcategory", ""),
            address=p.get("address", ""),
            phone=phone,
            website=p.get("website", ""),
            opening_hours=opening_hours,
            latitude=p.get("latitude", 0.0),
            longitude=p.get("longitude", 0.0),
            is_famous=p.get("is_famous", False),
            is_popular=p.get("is_popular", False),
        )
        db.add(place)

db.commit()
db.close()
print("Seeded places ✔")
