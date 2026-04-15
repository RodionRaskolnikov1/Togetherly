from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.city import City

router = APIRouter(prefix="/cities", tags=["cities"])

@router.get("/")
def get_cities(db: Session = Depends(get_db)): 
    cities = db.query(City).all()
    return [{"id": c.id, "name": c.name, "pincode" : c.pincode} for c in cities]