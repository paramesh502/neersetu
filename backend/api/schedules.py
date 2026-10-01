from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from models.models import IrrigationSchedule, Farmer
from db.database import get_session

router = APIRouter(prefix="/schedules", tags=["Schedules"])


class ScheduleRead(BaseModel):
    id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    farmer_plot: Optional[str] = None
    slot_start: datetime
    slot_end: datetime
    hours_allocated: float
    hours_used: float
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ScheduleCreate(BaseModel):
    farmer_db_id: int
    slot_start: datetime
    slot_end: datetime
    hours_allocated: float


@router.get("/", response_model=List[ScheduleRead])
def list_schedules(session: Session = Depends(get_session)):
    schedules = session.exec(
        select(IrrigationSchedule).order_by(IrrigationSchedule.slot_start)
    ).all()

    results = []
    for s in schedules:
        farmer = session.get(Farmer, s.farmer_id)
        results.append(ScheduleRead(
            id=s.id,
            farmer_id=s.farmer_id,
            farmer_name=farmer.name if farmer else None,
            farmer_plot=farmer.plot_number if farmer else None,
            slot_start=s.slot_start,
            slot_end=s.slot_end,
            hours_allocated=s.hours_allocated,
            hours_used=s.hours_used,
            status=s.status,
            notes=s.notes,
        ))
    return results


@router.get("/active")
def active_schedule(session: Session = Depends(get_session)):
    now = datetime.utcnow()
    active = session.exec(
        select(IrrigationSchedule)
        .where(IrrigationSchedule.slot_start <= now)
        .where(IrrigationSchedule.slot_end >= now)
        .where(IrrigationSchedule.status == "active")
    ).first()
    if not active:
        # Return next upcoming
        upcoming = session.exec(
            select(IrrigationSchedule)
            .where(IrrigationSchedule.slot_start > now)
            .where(IrrigationSchedule.status == "scheduled")
            .order_by(IrrigationSchedule.slot_start)
        ).first()
        if not upcoming:
            return {"active": None, "next": None}
        farmer = session.get(Farmer, upcoming.farmer_id)
        return {
            "active": None,
            "next": {
                "schedule_id": upcoming.id,
                "farmer_name": farmer.name if farmer else "Unknown",
                "plot": farmer.plot_number if farmer else "Unknown",
                "slot_start": upcoming.slot_start,
                "slot_end": upcoming.slot_end,
            },
        }
    farmer = session.get(Farmer, active.farmer_id)
    return {
        "active": {
            "schedule_id": active.id,
            "farmer_name": farmer.name if farmer else "Unknown",
            "plot": farmer.plot_number if farmer else "Unknown",
            "slot_start": active.slot_start,
            "slot_end": active.slot_end,
        },
        "next": None,
    }


@router.post("/", response_model=ScheduleRead, status_code=201)
def create_schedule(data: ScheduleCreate, session: Session = Depends(get_session)):
    farmer = session.get(Farmer, data.farmer_db_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    schedule = IrrigationSchedule(
        farmer_id=data.farmer_db_id,
        slot_start=data.slot_start,
        slot_end=data.slot_end,
        hours_allocated=data.hours_allocated,
        status="scheduled",
    )
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return ScheduleRead(
        id=schedule.id,
        farmer_id=schedule.farmer_id,
        farmer_name=farmer.name,
        farmer_plot=farmer.plot_number,
        slot_start=schedule.slot_start,
        slot_end=schedule.slot_end,
        hours_allocated=schedule.hours_allocated,
        hours_used=schedule.hours_used,
        status=schedule.status,
    )
