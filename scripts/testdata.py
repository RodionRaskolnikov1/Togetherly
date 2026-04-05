from database import SessionLocal, Base, engine
from models import Religion, Caste, SubCaste, City, Community

Base.metadata.create_all(bind=engine)

db = SessionLocal()

def seed_religions():
    religions = [
        "Hindu",
        "Muslim",
        "Jain",
        "Christian",
        "Sikh"
    ]

    for name in religions:
        if not db.query(Religion).filter_by(name=name).first():
            db.add(Religion(name=name))

    db.commit()
    print("Religions seeded")


def seed_castes():
    hindu = db.query(Religion).filter_by(name="Hindu").first()
    if not hindu:
        raise Exception("Hindu religion not found")

    castes = [
        "Patel",
        "Raval",
        "Brahmin",
        "Rajput"
    ]

    for name in castes:
        if not db.query(Caste).filter_by(
            name=name,
            religion_id=hindu.id
        ).first():
            db.add(Caste(name=name, religion_id=hindu.id))

    db.commit()
    print("Castes seeded")


def seed_sub_castes():
    patel = db.query(Caste).filter_by(name="Patel").first()
    if not patel:
        raise Exception("Patel caste not found")

    sub_castes = [
        "Kadva",
        "Kachhiya",
        "Leva"
    ]

    for name in sub_castes:
        if not db.query(SubCaste).filter_by(
            name=name,
            caste_id=patel.id
        ).first():
            db.add(SubCaste(name=name, caste_id=patel.id))

    db.commit()
    print("Sub-castes seeded")


# def seed_communities():
#     city = db.query(City).filter_by(name="Nadiad").first()
#     if not city:
#         raise Exception("City Nadiad not found")

#     hindu = db.query(Religion).filter_by(name="Hindu").first()
#     patel = db.query(Caste).filter_by(name="Patel").first()
#     kadva = db.query(SubCaste).filter_by(name="Kadva").first()

#     exists = db.query(Community).filter_by(
#         city_id=city.id,
#         religion_id=hindu.id,
#         caste_id=patel.id,
#         sub_caste_id=kadva.id
#     ).first()

#     if not exists:
#         db.add(Community(
#             city_id=city.id,
#             religion_id=hindu.id,
#             caste_id=patel.id,
#             sub_caste_id=kadva.id,
#             display_name="Nadiad Patel Kadva"
#         ))

#     db.commit()
#     print("Communities seeded")


if __name__ == "__main__":
    try:
        seed_religions()
        seed_castes()
        seed_sub_castes()
        # seed_communities()
    finally:
        db.close()
