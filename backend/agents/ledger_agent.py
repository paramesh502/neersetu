"""
Ledger Agent — commits the swap to the database, issues water credits, and updates schedules.
Writes immutable audit entries for every action.
"""
import uuid
import json
from datetime import datetime
from agents.state import NeerSetuState, AgentStep
from sqlmodel import Session, select
from db.database import engine
from models.models import (
    WaterCredit, CreditStatus, NegotiationRecord, SwapStatus,
    IrrigationSchedule, AuditLog, EmergencyRequest, RequestStatus, Farmer
)


def run_ledger_agent(state: NeerSetuState) -> NeerSetuState:
    step: AgentStep = {
        "agent": "Ledger Agent",
        "status": "running",
        "output": "",
        "details": {},
    }

    consent = state.get("consent_decision")
    if consent != "accepted":
        step["status"] = "complete"
        step["output"] = "Swap rejected — no ledger changes recorded."
        steps = list(state.get("agent_steps", []))
        steps.append(step)
        state["agent_steps"] = steps
        state["ledger_updated"] = False
        state["schedule_updated"] = False
        return state

    credit_id = f"CR-{uuid.uuid4().hex[:8].upper()}"
    actions = []

    with Session(engine) as session:
        # Resolve farmer DB rows by farmer_id string
        requesting_farmer = session.exec(
            select(Farmer).where(Farmer.farmer_id == state.get("farmer_id"))
        ).first()
        yielding_farmer = session.exec(
            select(Farmer).where(Farmer.farmer_id == state.get("yielding_farmer_id"))
        ).first()

        if not requesting_farmer or not yielding_farmer:
            step["status"] = "error"
            step["output"] = "Could not resolve farmer records in DB."
            steps = list(state.get("agent_steps", []))
            steps.append(step)
            state["agent_steps"] = steps
            state["error"] = "Ledger: farmer not found"
            return state

        # 1. Issue water credit to yielding farmer
        credit = WaterCredit(
            credit_id=credit_id,
            giving_farmer_id=requesting_farmer.id,  # requesting farmer "owes" back
            receiving_farmer_id=yielding_farmer.id,
            hours_given=state.get("hours_yielded", 0),
            hours_owed=state.get("compensation_hours", 0),
            status=CreditStatus.ACTIVE,
            notes=f"Emergency swap for {state.get('extracted_crop')} at {state.get('extracted_plot')}",
        )
        session.add(credit)
        session.flush()
        actions.append(f"Credit {credit_id} issued to {yielding_farmer.name}")

        # 2. Update water credit balance on yielding farmer
        yielding_farmer.water_credit_balance += state.get("compensation_hours", 0)

        # 3. Create negotiation record
        neg = NegotiationRecord(
            emergency_request_id=state.get("emergency_request_id"),
            requesting_farmer_id=requesting_farmer.id,
            yielding_farmer_id=yielding_farmer.id,
            hours_requested=state.get("extracted_hours", 3.0),
            hours_yielded=state.get("hours_yielded", 0),
            compensation_hours=state.get("compensation_hours", 0),
            yielding_farmer_eta=state.get("yielding_farmer_eta", 1.0),
            receiving_farmer_eta=state.get("flow_efficiency_index", 1.0),
            proposal_text=state.get("proposal_text", ""),
            status=SwapStatus.ACCEPTED,
            agent_steps=json.dumps(state.get("agent_steps", [])),
        )
        session.add(neg)
        session.flush()
        state["negotiation_id"] = neg.id
        actions.append(f"Negotiation record #{neg.id} created")

        # 4. Mark yielding farmer's nearest schedule as swapped
        yielding_schedule = session.exec(
            select(IrrigationSchedule)
            .where(IrrigationSchedule.farmer_id == yielding_farmer.id)
            .where(IrrigationSchedule.status == "scheduled")
            .order_by(IrrigationSchedule.slot_start)
        ).first()
        if yielding_schedule:
            yielding_schedule.status = "swapped"
            yielding_schedule.notes = f"Yielded to {requesting_farmer.name} — emergency swap"
            actions.append(f"Schedule slot updated → swapped for {yielding_farmer.name}")

        # 5. Update emergency request status
        if state.get("emergency_request_id"):
            req = session.get(EmergencyRequest, state["emergency_request_id"])
            if req:
                req.status = RequestStatus.ACCEPTED
                req.resolution_summary = state.get("consent_reason", "Swap accepted")
                req.decision_trace = json.dumps(state.get("agent_steps", []))
                req.updated_at = datetime.utcnow()

        # 6. Immutable audit log entries
        audit_entries = [
            AuditLog(
                event_type="swap_accepted",
                actor="ledger_agent",
                description=f"Swap: {yielding_farmer.name} yields {state.get('hours_yielded')} hrs to {requesting_farmer.name}",
                metadata_json=json.dumps({"credit_id": credit_id, "negotiation_id": neg.id}),
            ),
            AuditLog(
                event_type="credit_issued",
                actor="ledger_agent",
                description=f"Credit {credit_id}: {state.get('compensation_hours')} hrs owed to {yielding_farmer.name}",
                metadata_json=json.dumps({"credit_id": credit_id, "farmer": yielding_farmer.farmer_id}),
            ),
        ]
        for entry in audit_entries:
            session.add(entry)

        session.commit()

    state["credit_id"] = credit_id
    state["ledger_updated"] = True
    state["schedule_updated"] = True

    step["status"] = "complete"
    step["output"] = f"Ledger updated. Credit {credit_id} issued. {len(actions)} actions recorded."
    step["details"] = {"credit_id": credit_id, "actions": actions}

    steps = list(state.get("agent_steps", []))
    steps.append(step)
    state["agent_steps"] = steps
    return state
