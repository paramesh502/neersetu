from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import json

from models.models import NegotiationRecord, Farmer, SwapStatus
from db.database import get_session

router = APIRouter(prefix="/negotiations", tags=["Negotiations"])


class NegotiationRead(BaseModel):
    id: int
    emergency_request_id: Optional[int]
    requesting_farmer_id: Optional[int]
    requesting_farmer_name: Optional[str]
    requesting_farmer_plot: Optional[str]
    yielding_farmer_id: Optional[int]
    yielding_farmer_name: Optional[str]
    yielding_farmer_plot: Optional[str]
    hours_requested: float
    hours_yielded: float
    compensation_hours: float
    yielding_farmer_eta: float
    receiving_farmer_eta: float
    proposal_text: str
    status: str
    agent_steps: Optional[List[dict]] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[NegotiationRead])
def list_negotiations(session: Session = Depends(get_session)):
    records = session.exec(
        select(NegotiationRecord).order_by(NegotiationRecord.created_at.desc())
    ).all()

    results = []
    for rec in records:
        req_farmer = session.get(Farmer, rec.requesting_farmer_id)
        yld_farmer = session.get(Farmer, rec.yielding_farmer_id)
        steps = []
        if rec.agent_steps:
            try:
                steps = json.loads(rec.agent_steps)
            except Exception:
                steps = []
        results.append(NegotiationRead(
            id=rec.id,
            emergency_request_id=rec.emergency_request_id,
            requesting_farmer_id=rec.requesting_farmer_id,
            requesting_farmer_name=req_farmer.name if req_farmer else None,
            requesting_farmer_plot=req_farmer.plot_number if req_farmer else None,
            yielding_farmer_id=rec.yielding_farmer_id,
            yielding_farmer_name=yld_farmer.name if yld_farmer else None,
            yielding_farmer_plot=yld_farmer.plot_number if yld_farmer else None,
            hours_requested=rec.hours_requested,
            hours_yielded=rec.hours_yielded,
            compensation_hours=rec.compensation_hours,
            yielding_farmer_eta=rec.yielding_farmer_eta,
            receiving_farmer_eta=rec.receiving_farmer_eta,
            proposal_text=rec.proposal_text,
            status=rec.status,
            agent_steps=steps,
            created_at=rec.created_at,
        ))
    return results


@router.get("/{negotiation_id}", response_model=NegotiationRead)
def get_negotiation(negotiation_id: int, session: Session = Depends(get_session)):
    rec = session.get(NegotiationRecord, negotiation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Negotiation not found")

    req_farmer = session.get(Farmer, rec.requesting_farmer_id)
    yld_farmer = session.get(Farmer, rec.yielding_farmer_id)
    steps = []
    if rec.agent_steps:
        try:
            steps = json.loads(rec.agent_steps)
        except Exception:
            steps = []

    return NegotiationRead(
        id=rec.id,
        emergency_request_id=rec.emergency_request_id,
        requesting_farmer_id=rec.requesting_farmer_id,
        requesting_farmer_name=req_farmer.name if req_farmer else None,
        requesting_farmer_plot=req_farmer.plot_number if req_farmer else None,
        yielding_farmer_id=rec.yielding_farmer_id,
        yielding_farmer_name=yld_farmer.name if yld_farmer else None,
        yielding_farmer_plot=yld_farmer.plot_number if yld_farmer else None,
        hours_requested=rec.hours_requested,
        hours_yielded=rec.hours_yielded,
        compensation_hours=rec.compensation_hours,
        yielding_farmer_eta=rec.yielding_farmer_eta,
        receiving_farmer_eta=rec.receiving_farmer_eta,
        proposal_text=rec.proposal_text,
        status=rec.status,
        agent_steps=steps,
        created_at=rec.created_at,
    )
