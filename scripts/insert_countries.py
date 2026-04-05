from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models.country import Country

Base.metadata.create_all(bind=engine)

COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola",
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan",
    "Bahamas", "Bahrain", "Bangladesh", "Belarus", "Belgium",
    "Bhutan", "Bolivia", "Brazil", "Bulgaria", "Cambodia",
    "Canada", "Chile", "China", "Colombia", "Croatia",
    "Cuba", "Cyprus", "Czech Republic", "Denmark", "Dominican Republic",
    "Ecuador", "Egypt", "Estonia", "Ethiopia", "Finland",
    "France", "Germany", "Ghana", "Greece", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq",
    "Ireland", "Israel", "Italy", "Japan", "Jordan",
    "Kenya", "Kuwait", "Laos", "Latvia", "Lebanon",
    "Lithuania", "Luxembourg", "Malaysia", "Maldives", "Mexico",
    "Mongolia", "Morocco", "Myanmar", "Nepal", "Netherlands",
    "New Zealand", "Nigeria", "North Korea", "Norway", "Oman",
    "Pakistan", "Philippines", "Poland", "Portugal", "Qatar",
    "Romania", "Russia", "Saudi Arabia", "Singapore", "South Africa",
    "South Korea", "Spain", "Sri Lanka", "Sweden", "Switzerland",
    "Thailand", "Turkey", "Ukraine", "United Arab Emirates",
    "United Kingdom", "United States", "Vietnam", "Yemen", "Zimbabwe"
]

def insert_countries():
    db: Session = SessionLocal()
    try:
        existing = {
            s.name.lower()
            for s in db.query(Country.name).all()
        }

        new_records = [
            Country(name=country)
            for country in COUNTRIES
            if country.lower() not in existing
        ]

        db.bulk_save_objects(new_records)
        db.commit()

        print(f"Inserted {len(new_records)} countries")

    except Exception as e:
        db.rollback()
        print("Insert failed:", e)

    finally:
        db.close()

if __name__ == "__main__":
    insert_countries()
