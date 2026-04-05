import requests
import time
import uuid
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models.universities import University

# Ensure tables exist
Base.metadata.create_all(bind=engine)

API_KEY = "579b464db66ec23bdd00000148cb9630c4784c5e5f077b6e692ba694"
RESOURCE_ID = "44bea382-c525-4740-8a07-04bd20a99b52"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

STATE_NAME = "Gujarat"
LIMIT = 50   # smaller batch size to reduce server resets
offset = 0

def insert_universities(records):
    db: Session = SessionLocal()
    try:
        for record in records:
            uni = University(
                university_name=record.get("university_name"),
                college_name=record.get("college_name"),
                state_name=record.get("state_name"),
                college_type=record.get("college_type"),
                district_name=record.get("district_name"),
            )
            db.add(uni)
        db.commit()
        print(f"Inserted {len(records)} records into database")
    except Exception as e:
        db.rollback()
        print("DB insert Error:", e)
    finally:
        db.close()

while True:
    params = {
        "api-key": API_KEY,
        "format": "json",
        "filters[state_name]": STATE_NAME,
        "limit": LIMIT,
        "offset": offset
    }

    try:
        # Force new connection each time to avoid server closing persistent sockets
        response = requests.get(BASE_URL, params=params, headers={"Connection": "close"}, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Request error at offset {offset}: {e}")
        break

    try:
        data = response.json()
    except ValueError:
        print("Invalid JSON response")
        break

    records = data.get("records", [])
    if not records:
        break

    insert_universities(records)
    print(f"Fetched {len(records)} records. Offset now {offset + LIMIT}")

    offset += LIMIT
    time.sleep(1)  # short pause to avoid rate limiting

print("Data import complete.")