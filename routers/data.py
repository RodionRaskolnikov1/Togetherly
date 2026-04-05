from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

from models import (
    City, Country, State,
    University, Religion, Caste, SubCaste
)

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/countries")
def get_countires(db: Session = Depends(get_db)): 
    countries = db.query(Country).all()
    return [{"id": c.id, "name": c.name} for c in countries]


@router.get("/states")
def get_states(db: Session = Depends(get_db)): 
    states = (
        db.query(State.id, State.name)
        .join(Country, State.country_id == Country.id)
        .filter(Country.name == "India")
        .all()
    )
    return [{"id": s.id, "name": s.name} for s in states] 


@router.get("/cities")
def get_cities(state_id : str, db: Session = Depends(get_db)): 
    cities = db.query(City.id, City.name, City.pincode).filter(City.state_id == state_id).all()
    return [{"id": c.id, "name": c.name, "pincode" : c.pincode} for c in cities]


@router.get("/universities")
def get_universities(db: Session = Depends(get_db)): 
    universities1 = db.query(University).all()
    return [{"id": c.id, "university_name": c.university_name, "college_name": c.college_name} for c in universities1]


@router.get("/religions")
def get_religions(db: Session = Depends(get_db)): 
    religions = db.query(Religion).all()
    return [{"id": r.id, "name": r.name} for r in religions]

@router.get("/castes")
def get_castes(religion_id: str, db: Session = Depends(get_db)): 
    caste = db.query(Caste.id, Caste.name).filter(Caste.religion_id == religion_id).all()
    return [{"id": c.id, "name": c.name} for c in caste]

@router.get("/sub-castes")
def get_sub_castes(caste_id: str, db: Session = Depends(get_db)):
    sub_caste = db.query(SubCaste.id, SubCaste.name).filter(SubCaste.caste_id == caste_id).all()
    return [{"id": c.id, "name": c.name} for c in sub_caste]

