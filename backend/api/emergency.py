"""Emergency request API — receives raw farmer messages, runs the full LangGraph pipeline."""
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from models.models import EmergencyRequest, RequestStatus, Farmer
from db.database import get_session

router = APIRouter(prefix="/emergency", tags=["Emergency Requests"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class EmergencyRequestCreate(BaseModel):
    farmer_id: str        # e.g. "F006"
    raw_message: str


class EmergencyRequestRead(BaseModel):
    id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    farmer_plot: Optional[str] = None
    raw_message: str
    extracted_crop: Optional[str] = None
    extracted_urgency: Optional[str] = None
    extracted_hours: Optional[float] = None
    extracted_plot: Optional[str] = None
    status: str
    fwos_score: Optional[float] = None
    resolution_summary: Optional[str] = None
    decision_trace: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PipelineResponse(BaseModel):
    emergency_request_id: int
    status: str
    fwos_score: Optional[float]
    consent_decision: Optional[str]
    consent_reason: Optional[str]
    proposal_text: Optional[str]
    chat_notification: Optional[str]
    sms_notification: Optional[str]
    ivr_script: Optional[str]
    print_schedule: Optional[str]
    fairness_explanation: Optional[str]
    credit_id: Optional[str]
    compensation_hours: Optional[float]
    hours_yielded: Optional[float]
    yielding_farmer_name: Optional[str]
    fwos_breakdown: Optional[dict]
    agent_steps: List[dict]
    error: Optional[str] = None


# ─── Helper: find best yielding farmer ────────────────────────────────────────

def _find_yielding_farmer(requesting_farmer: Farmer, session: Session) -> Optional[Farmer]:
    """
    Find the most suitable farmer to yield water:
    - Must be upstream (lower canal_position)
    - Has a scheduled slot
    - Has higher η than requesting farmer
    """
    farmers = session.exec(
        select(Farmer)
        .where(Farmer.canal_position < requesting_farmer.canal_position)
        .order_by(Farmer.canal_position.desc())   # start from closest upstream
    ).all()

    from models.models import IrrigationSchedule
    for farmer in farmers:
        slot = session.exec(
            select(IrrigationSchedule)
            .where(IrrigationSchedule.farmer_id == farmer.id)
            .where(IrrigationSchedule.status == "scheduled")
        ).first()
        if slot:
            return farmer

    # Fallback: any farmer with an available slot
    for farmer in farmers:
        if farmer.id != requesting_farmer.id:
            return farmer

    return None


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[EmergencyRequestRead])
def list_requests(session: Session = Depends(get_session)):
    requests = session.exec(
        select(EmergencyRequest).order_by(EmergencyRequest.created_at.desc())
    ).all()
    results = []
    for req in requests:
        farmer = session.get(Farmer, req.farmer_id)
        results.append(EmergencyRequestRead(
            id=req.id,
            farmer_id=req.farmer_id,
            farmer_name=farmer.name if farmer else None,
            farmer_plot=farmer.plot_number if farmer else None,
            raw_message=req.raw_message,
            extracted_crop=req.extracted_crop,
            extracted_urgency=req.extracted_urgency,
            extracted_hours=req.extracted_hours,
            extracted_plot=req.extracted_plot,
            status=req.status,
            fwos_score=req.fwos_score,
            resolution_summary=req.resolution_summary,
            decision_trace=req.decision_trace,
            created_at=req.created_at,
        ))
    return results


@router.get("/{request_id}", response_model=EmergencyRequestRead)
def get_request(request_id: int, session: Session = Depends(get_session)):
    req = session.get(EmergencyRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    farmer = session.get(Farmer, req.farmer_id)
    return EmergencyRequestRead(
        id=req.id,
        farmer_id=req.farmer_id,
        farmer_name=farmer.name if farmer else None,
        farmer_plot=farmer.plot_number if farmer else None,
        raw_message=req.raw_message,
        extracted_crop=req.extracted_crop,
        extracted_urgency=req.extracted_urgency,
        extracted_hours=req.extracted_hours,
        extracted_plot=req.extracted_plot,
        status=req.status,
        fwos_score=req.fwos_score,
        resolution_summary=req.resolution_summary,
        decision_trace=req.decision_trace,
        created_at=req.created_at,
    )


@router.post("/process", response_model=PipelineResponse)
def process_emergency(data: EmergencyRequestCreate, session: Session = Depends(get_session)):
    """
    Main endpoint: runs the full 6-agent LangGraph pipeline and returns results.
    """
    from agents.pipeline import neersetu_pipeline

    # Resolve farmer
    farmer = session.exec(
        select(Farmer).where(Farmer.farmer_id == data.farmer_id)
    ).first()
    if not farmer:
        raise HTTPException(status_code=404, detail=f"Farmer {data.farmer_id} not found")

    # Store raw emergency request
    req = EmergencyRequest(
        farmer_id=farmer.id,
        raw_message=data.raw_message,
        status=RequestStatus.NEGOTIATING,
        extracted_plot=farmer.plot_number,
    )
    session.add(req)
    session.commit()
    session.refresh(req)

    # Find yielding farmer and inject into state
    yielding = _find_yielding_farmer(farmer, session)
    yielding_data = None
    if yielding:
        yielding_data = {
            "farmer_id": yielding.farmer_id,
            "name": yielding.name,
            "canal_position": yielding.canal_position,
            "eta": yielding.flow_efficiency_index,
            "plot": yielding.plot_number,
        }

    # Build initial state
    initial_state = {
        "raw_message": data.raw_message,
        "farmer_id": data.farmer_id,
        "farmer_name": farmer.name,
        "canal_position": farmer.canal_position,
        "flow_efficiency_index": farmer.flow_efficiency_index,
        "historical_deficit": farmer.historical_deficit,
        "missed_turns": farmer.missed_turns,
        "extracted_plot": farmer.plot_number,
        "emergency_request_id": req.id,
        "db_farmer_data": {
            "farmer_id": farmer.farmer_id,
            "name": farmer.name,
            "plot": farmer.plot_number,
            "eta": farmer.flow_efficiency_index,
        },
        "db_yielding_farmer_data": yielding_data,
        "agent_steps": [],
        "completed": False,
    }

    # Run pipeline
    try:
        result = neersetu_pipeline.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    # Update emergency request with results
    req.extracted_crop = result.get("extracted_crop")
    req.extracted_urgency = result.get("extracted_urgency")
    req.extracted_hours = result.get("extracted_hours")
    req.fwos_score = result.get("fwos_score")
    req.decision_trace = json.dumps(result.get("agent_steps", []))
    req.updated_at = datetime.utcnow()

    consent = result.get("consent_decision", "accepted")
    req.status = RequestStatus.ACCEPTED if consent == "accepted" else RequestStatus.REJECTED
    req.resolution_summary = result.get("consent_reason", "")

    session.add(req)
    session.commit()

    return PipelineResponse(
        emergency_request_id=req.id,
        status=req.status,
        fwos_score=result.get("fwos_score"),
        consent_decision=result.get("consent_decision"),
        consent_reason=result.get("consent_reason"),
        proposal_text=result.get("proposal_text"),
        chat_notification=result.get("chat_notification"),
        sms_notification=result.get("sms_notification"),
        ivr_script=result.get("ivr_script"),
        print_schedule=result.get("print_schedule"),
        fairness_explanation=result.get("fairness_explanation"),
        credit_id=result.get("credit_id"),
        compensation_hours=result.get("compensation_hours"),
        hours_yielded=result.get("hours_yielded"),
        yielding_farmer_name=result.get("yielding_farmer_name"),
        fwos_breakdown=result.get("fwos_breakdown"),
        agent_steps=result.get("agent_steps", []),
        error=result.get("error"),
    )
