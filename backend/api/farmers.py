from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from models.models import Farmer, CropType
from db.database import get_session

router = APIRouter(prefix="/farmers", tags=["Farmers"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class FarmerCreate(BaseModel):
    farmer_id: str
    name: str
    phone: str
    plot_number: str
    canal_position: int
    crop_type: CropType
    flow_efficiency_index: float


class FarmerRead(BaseModel):
    id: int
    farmer_id: str
    name: str
    phone: str
    plot_number: str
    canal_position: int
    crop_type: str
    flow_efficiency_index: float
    water_credit_balance: float
    total_hours_allocated: float
    total_hours_used: float
    historical_deficit: float
    missed_turns: int

    class Config:
        from_attributes = True


class FarmerUpdate(BaseModel):
    water_credit_balance: Optional[float] = None
    historical_deficit: Optional[float] = None
    missed_turns: Optional[int] = None
    flow_efficiency_index: Optional[float] = None


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[FarmerRead])
def list_farmers(session: Session = Depends(get_session)):
    farmers = session.exec(select(Farmer).order_by(Farmer.canal_position)).all()
    return farmers


@router.get("/{farmer_id}", response_model=FarmerRead)
def get_farmer(farmer_id: str, session: Session = Depends(get_session)):
    farmer = session.exec(
        select(Farmer).where(Farmer.farmer_id == farmer_id)
    ).first()
    if not farmer:
        raise HTTPException(status_code=404, detail=f"Farmer {farmer_id} not found")
    return farmer


@router.post("/", response_model=FarmerRead, status_code=201)
def create_farmer(data: FarmerCreate, session: Session = Depends(get_session)):
    existing = session.exec(
        select(Farmer).where(Farmer.farmer_id == data.farmer_id)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Farmer ID already exists")
    farmer = Farmer(**data.model_dump())
    session.add(farmer)
    session.commit()
    session.refresh(farmer)
    return farmer


@router.patch("/{farmer_id}", response_model=FarmerRead)
def update_farmer(
    farmer_id: str,
    data: FarmerUpdate,
    session: Session = Depends(get_session),
):
    farmer = session.exec(
        select(Farmer).where(Farmer.farmer_id == farmer_id)
    ).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(farmer, key, value)
    session.add(farmer)
    session.commit()
    session.refresh(farmer)
    return farmer


@router.get("/{farmer_id}/stats")
def farmer_stats(farmer_id: str, session: Session = Depends(get_session)):
    farmer = session.exec(
        select(Farmer).where(Farmer.farmer_id == farmer_id)
    ).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {
        "farmer_id": farmer.farmer_id,
        "name": farmer.name,
        "water_credit_balance": farmer.water_credit_balance,
        "historical_deficit": farmer.historical_deficit,
        "missed_turns": farmer.missed_turns,
        "total_hours_allocated": farmer.total_hours_allocated,
        "total_hours_used": farmer.total_hours_used,
        "efficiency_ratio": (
            round(farmer.total_hours_used / farmer.total_hours_allocated, 2)
            if farmer.total_hours_allocated > 0 else 0.0
        ),
    }
