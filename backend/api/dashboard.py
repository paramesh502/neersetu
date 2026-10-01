"""Dashboard aggregation endpoint — single call for the main dashboard."""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from datetime import datetime

from models.models import (
    Farmer, IrrigationSchedule, EmergencyRequest, WaterCredit,
    NegotiationRecord, CreditStatus, RequestStatus
)
from db.database import get_session
from agents.fairness_agent import compute_fwos

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/")
def dashboard_summary(session: Session = Depends(get_session)):
    now = datetime.utcnow()

    # Farmers
    farmers = session.exec(select(Farmer).order_by(Farmer.canal_position)).all()

    # Schedules
    all_schedules = session.exec(
        select(IrrigationSchedule).order_by(IrrigationSchedule.slot_start)
    ).all()
    upcoming = [s for s in all_schedules if s.slot_start > now and s.status == "scheduled"][:6]

    # Active farmer
    active_sched = next(
        (s for s in all_schedules
         if s.slot_start <= now <= s.slot_end and s.status == "active"),
        None,
    )
    active_farmer = None
    if active_sched:
        f = session.get(Farmer, active_sched.farmer_id)
        if f:
            active_farmer = {"name": f.name, "plot": f.plot_number, "eta": f.flow_efficiency_index}

    # Emergency requests
    emergency_requests = session.exec(
        select(EmergencyRequest)
        .where(EmergencyRequest.status.in_([RequestStatus.PENDING, RequestStatus.NEGOTIATING]))
    ).all()

    # Credits
    credits = session.exec(
        select(WaterCredit).where(WaterCredit.status == CreditStatus.ACTIVE)
    ).all()

    # Negotiations
    negotiations = session.exec(
        select(NegotiationRecord).order_by(NegotiationRecord.created_at.desc()).limit(5)
    ).all()

    # Build farmer cards with FWOS
    farmer_cards = []
    for f in farmers:
        fwos, _ = compute_fwos(
            canal_position=f.canal_position,
            eta=f.flow_efficiency_index,
            historical_deficit=f.historical_deficit,
            missed_turns=f.missed_turns,
            urgency="medium",
        )
        farmer_cards.append({
            "farmer_id": f.farmer_id,
            "name": f.name,
            "plot": f.plot_number,
            "canal_position": f.canal_position,
            "crop_type": f.crop_type,
            "eta": f.flow_efficiency_index,
            "fwos": fwos,
            "credit_balance": f.water_credit_balance,
            "historical_deficit": f.historical_deficit,
            "missed_turns": f.missed_turns,
        })

    # Upcoming schedule with farmer names
    schedule_items = []
    for s in upcoming:
        f = session.get(Farmer, s.farmer_id)
        schedule_items.append({
            "schedule_id": s.id,
            "farmer_name": f.name if f else "Unknown",
            "plot": f.plot_number if f else "?",
            "eta": f.flow_efficiency_index if f else 1.0,
            "slot_start": s.slot_start.isoformat(),
            "slot_end": s.slot_end.isoformat(),
            "hours": s.hours_allocated,
            "status": s.status,
        })

    return {
        "summary": {
            "total_farmers": len(farmers),
            "active_emergency_requests": len(emergency_requests),
            "active_credits": len(credits),
            "total_credit_hours_owed": round(sum(c.hours_owed for c in credits), 2),
            "recent_negotiations": len(negotiations),
        },
        "active_farmer": active_farmer,
        "upcoming_schedule": schedule_items,
        "farmer_cards": farmer_cards,
        "emergency_requests": [
            {
                "id": req.id,
                "farmer_id": req.farmer_id,
                "status": req.status,
                "urgency": req.extracted_urgency,
                "crop": req.extracted_crop,
                "created_at": req.created_at.isoformat(),
            }
            for req in emergency_requests
        ],
        "canal_flow": [
            {
                "position": f.canal_position,
                "plot": f.plot_number,
                "farmer": f.name,
                "eta": f.flow_efficiency_index,
                "flow_percent": round(f.flow_efficiency_index * 100, 0),
            }
            for f in farmers
        ],
    }
