from sqlalchemy.orm import Session
from database import SessionLocal
from models.state import State
from models.country import Country

INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]


def insert_indian_states():
    db: Session = SessionLocal()

    try:
        india = db.query(Country).filter(Country.name == "India").first()
        if not india:
            raise Exception("India not found in countries table")
        existing_states = {
            s.name.lower()
            for s in db.query(State.name).filter(State.country_id == india.id).all()
        }
        new_states = [
            State(name=state, country_id=india.id)
            for state in INDIAN_STATES
            if state.lower() not in existing_states
        ]
        db.bulk_save_objects(new_states)
        db.commit()

        print(f"Inserted {len(new_states)} Indian states")
        
    except Exception as e:
        db.rollback()
        print("Insert failed:", e)

    finally:
        db.close()
        
if __name__ == "__main__":
    insert_indian_states()
        