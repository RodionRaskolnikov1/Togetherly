import uuid
import requests, json, time, re
from database import SessionLocal, Base, engine
from models.city import City
from models.state import State
from sqlalchemy.exc import InterfaceError
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)

API_KEY = "579b464db66ec23bdd00000148cb9630c4784c5e5f077b6e692ba694"
RESOURCE_ID = "5c2f62fe-5afa-4119-a499-fec9d604d5bd"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

STATE_NAME = "Gujarat"
LIMIT = 8841 
all_gujarat_cities = []
offset = 0
total_records = 1
print(f"Starting data fetch for {STATE_NAME}...")

def insert_cities(records):
    db: Session = SessionLocal()
    
    try:
        gujarat = db.query(State).filter(State.name == "Gujarat").first()
        if not gujarat:
            raise Exception("State 'Gujarat' not found in states table")
        
        # Build all city objects first
        cities_to_insert = []
        seen = set()  # avoid duplicates in memory

        for record in records:
            raw_name = record.get("officename")
            pincode = record.get("pincode")
            
            if not raw_name or not pincode:
                continue
            
            name = re.sub(r"\b(BO|SO|HO|MDG|RMS|B.O)$", "", raw_name).strip()
            pincode = str(pincode).strip()
            if not pincode.isdigit():
                continue
            
            key = (name, pincode, gujarat.id)
            if key in seen:
                continue
            seen.add(key)

            cities_to_insert.append(City(
                name=name,
                pincode=pincode,
                state_id=gujarat.id
            ))

        # Single bulk insert, ignore conflicts
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        if cities_to_insert:
            stmt = pg_insert(City).values([
                {"id": str(uuid.uuid4()), "name": c.name, "pincode": c.pincode, "state_id": c.state_id}
                for c in cities_to_insert
            ]).on_conflict_do_nothing()  # skips duplicates automatically
            
            db.execute(stmt)
            db.commit()
            print(f"Inserted {len(cities_to_insert)} cities successfully")

    except Exception as e:
        db.rollback()
        print("DB insert Error: ", e)
    finally:
        db.close()

while offset < total_records:
    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": LIMIT,
        "offset": offset,
        "filters[statename]": STATE_NAME
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()
        if offset == 0:
            total_records = int(data.get("total", 0))
            print(f"Total records found for {STATE_NAME}: {total_records}")

        records = data.get("records", [])
        all_gujarat_cities.extend(records)

        print(f"Fetched {len(records)} records. Current total: {len(all_gujarat_cities)} / {total_records}")

        offset += LIMIT
        time.sleep(1)

    except Exception as e:
        print("Error during API fetch:", e)
        break
    
if all_gujarat_cities:
    print(f"\nSuccessfully fetched {len(all_gujarat_cities)} records.")
    print("\nExample Record:")
    print(json.dumps(all_gujarat_cities[0], indent=2))

    insert_cities(all_gujarat_cities)

else:
    print("No data fetched.")